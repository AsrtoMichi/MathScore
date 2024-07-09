#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GUI

from tkinter import IntVar, Tk, Toplevel, Canvas, StringVar, Entry, Label
from tkinter.ttk import Frame, Button, Scrollbar, Combobox
from tkinter.filedialog import askopenfilename, asksaveasfile
from tkinter.messagebox import askokcancel, showerror, showwarning
from _tkinter import TclError

# os
from threading import Thread
from subprocess import run
from sched import scheduler
from time import time as t_time, sleep
from sys import exit as sys_exit


# .ini reading
from configparser import ConfigParser, NoSectionError, ParsingError, NoOptionError
from ast import literal_eval
from os.path import join, dirname, abspath, exists


# Gestion of errors:
#   Configuration errors 1:
#       10 No .ini file was given
#       11 Unable to load data
#       12 Error reading the configuration file
# 2 Conclusion during the competions


def set_icon(window: Tk):
    """
    Set the icon of a windows
    """
    try:
        window.iconbitmap(abspath(join(dirname(__file__), 'MathScore.ico')))
    except (FileNotFoundError, IOError, PermissionError):
        pass


class Recorder:

    """
    This class is used for save:
    - values of question in the time
    - tootal points of a team in the time
    - answer given by a team
    - jolly chosen for a team     
    """

    def __init__(self, names_teams: list, number_of_question_tuple: tuple, total_time: int, base_points: int, base_value_question: int):
        self._jolly = {name: None for name in names_teams}
        self._answer = {name: []
                        for name in names_teams}
        self._values_questions = [None] + [[
            (total_time, base_value_question)] for _ in number_of_question_tuple]

        self._total_teams = {name: [(total_time, base_points)]
                             for name in names_teams}

    def record_jolly(self, name_team: str, question: int):
        self._jolly[name_team] = question

    def record_answer(self, name_team: str, time: int, answer: int):
        self._answer[name_team].append((time, answer))

    def record_values_questions(self, question: int, time: int, value: int):
        if self._values_questions[question][-1][1] != value:
            self._values_questions[question].append((time, value))

    def record_total_teams(self, name_team: str, time: int, value: int):
        if self._total_teams[name_team][-1][1] != value:
            self._total_teams[name_team].append((time, value))

    def __str__(self):
        return str((self._jolly, self._answer, self._values_questions, self._total_teams, self._values_questions[1][0][0]))


class Main(Tk):

    """
    That class is the main window: here are showed poits
    """

    def __init__(self):

        # serch the ini file in the same directory
        # abspath is use to prevent problem the exe convrsion

        ini_file_path = abspath(join(dirname(__file__), 'Config.ini'))

        if not exists(ini_file_path):

            # if ther isn't the ini file in the same path ask to the user to select the file
            ini_file_path = askopenfilename(
                filetypes=[("Configuration files", "*.ini")])

            if ini_file_path == "":

                showerror(
                    "Error", "No .ini file was given.")
                sys_exit(10)

        try:
            # ceck if is possible read the file
            open(ini_file_path, "r")

        except (FileNotFoundError, IOError, PermissionError):
            showerror(
                "Error", "Unable to find or read the config.ini file")
            sys_exit(11)

        else:
            config = ConfigParser()
            config.read(ini_file_path)

        try:

            self.NAMES_TEAMS = tuple(
                config.get('Teams', 'teams').split(', '))

            self._TOTAL_TIME = self._timer_seconds = config.getint(
                'Timer', 'time')*60

            self._TIME_FOR_JOLLY = config.getint('Timer', 'time_for_jolly')*60

            # the DERIVE is the minum number of question to block the grow of the value of a question
            self._DERIVE = config.getint('Points', 'derive')

            self._BONUS_ANSWER = literal_eval(
                config.get('Points', 'bonus_answer'))
            self._N_BONUS_ANSWER = len(self._BONUS_ANSWER)
            self._BONUS_FULLED = literal_eval(
                config.get('Points', 'bonus_fulled'))
            self._N_BONUS_FULLED = len(self._BONUS_FULLED)

            # 0: solution
            # 1: correct
            # 2: incorrect
            # 3: value

            value = config.getint('Points', 'vantage')

            self._solutions = [None] + [
                [solution,  0,  0, value]
                for solution in literal_eval(config.get('Solutions', 'solutions'))
            ]

            self._NUMBER_OF_QUESTIONS = len(self._solutions)-1

            self._NUMBER_OF_QUESTIONS_RANGE_1 = range(
                1, self._NUMBER_OF_QUESTIONS+1)

            # 0: errors
            # 1: status
            # 2: jolly
            # 3: bonus

            # list point, bonus, n_fulled

            self._list_point = {
                name: [self._NUMBER_OF_QUESTIONS * 10, [0, 0, 2, 0]] + [[0, 0, 1, 0]
                                                                        for _ in range(
                    1, self._NUMBER_OF_QUESTIONS)
                ] for name in self.NAMES_TEAMS}

            self._fulled = 0

            self._recorder = Recorder(
                self.NAMES_TEAMS, self._NUMBER_OF_QUESTIONS_RANGE_1, self._TOTAL_TIME, self._NUMBER_OF_QUESTIONS * 10, value)

        except (NoSectionError, ValueError, ParsingError, NoOptionError, SyntaxError):

            showerror(
                "Error", "An error orccured reading the config.ini file")
            sys_exit(12)

        else:

            # creation Main window and castomization
            super().__init__()
            self.title("Competitors")
            self.geometry('1600x630')
            self.resizable(True, False)
            set_icon(self)

            # widget costruction
            self.timer_label = Label(self, font=('Helvetica', 18, 'bold'))
            self.timer_label.pack()
            self.generate_clock()

            self.main_button = Button(
                self, text="Start", command=self.start_competition)
            self.main_button.pack()

            points_label = Frame(self, width=1550, height=600)
            points_label.pack()

            # Creazione del canvas all'interno dell'etichetta dei punti
            canvas = Canvas(
                points_label,
                width=1550,
                height=600,
                scrollregion=(0, 0, 1550, len(self.NAMES_TEAMS) * 26),
            )
            canvas.pack(side='left', expand=True, fill='both')

            # Aggiunta di una barra di scorrimento verticale
            scrollbar = Scrollbar(points_label, command=canvas.yview)
            scrollbar.pack(side='right', fill='y')

            canvas.configure(yscrollcommand=scrollbar.set)

            self.frame_point = Frame(
                canvas, width=1800, height=len(self.NAMES_TEAMS) * 26)
            canvas.create_window((0, 0), window=self.frame_point, anchor='nw')

            self.s = scheduler(t_time, sleep)

            self.s.enter(self._TOTAL_TIME - 30, 3, lambda: [
                widget.grid_forget() for widget in self.frame_point.winfo_children()])

            self.s.enter(self._TOTAL_TIME, 3, lambda: self.main_button.configure(
                state='normal', text="Show ranking", command=self.show_ranking))

            self.s.enter(self._TOTAL_TIME, 4, self.timer_label.destroy)

            for time in range(self._TOTAL_TIME - 30, self._TOTAL_TIME):
                self.s.enter(time, 2, self.update_main)

            for time in range(1, self._TOTAL_TIME - 30):
                self.s.enter(time, 1, self.update_entry)
                self.s.enter(time, 2, self.update_main)

            for time in range(60, self._TOTAL_TIME - 1200, 60):

                self.s.enter(time, 1, lambda: [
                    self._solutions[question][3] + 1
                    for question in self._NUMBER_OF_QUESTIONS_RANGE_1
                    if self._solutions[question][1] < self._DERIVE
                ])

            self.entry_quetion_x_team = [
                [None] + [Entry(self.frame_point, width=6, bd=5, state='readonly', readonlybackground='white')
                          for _ in self._NUMBER_OF_QUESTIONS_RANGE_1]
                for _ in self.NAMES_TEAMS]

            self.stringvar_question_x_team = [
                [None] + [IntVar() for _ in self._NUMBER_OF_QUESTIONS_RANGE_1] for _ in self.NAMES_TEAMS]

            self.stringvar_question = [None] + [IntVar()
                                                for _ in self._NUMBER_OF_QUESTIONS_RANGE_1]

            self.stringvar_start_row = [
                [StringVar(), IntVar()] for _ in self.NAMES_TEAMS]

            self.protocol('WM_DELETE_WINDOW', lambda: sys_exit(2 if self._timer_seconds !=
                                                               0 else 0) if askokcancel("Closing confirm", "All data can be losted.") else None)

    # method about runtime

    def update_main(self):

        self._timer_seconds -= 1
        self.generate_clock()

        for team in self.NAMES_TEAMS:
            self._recorder.record_total_teams(
                team, self._timer_seconds, self.total_team_point(team))

        for question in self._NUMBER_OF_QUESTIONS_RANGE_1:
            self._recorder.record_values_questions(
                question, self._timer_seconds, self.point_answer(question))

        # methods about the progress ot time

    def start_competition(self):
        """
        Start the timer and block start buttom
        """
        self.arbiter_GUI = Arbiter_GUI(self)
        self.jolly_GUI = Jolly_GUI(self)

        self.s.enter(self._TOTAL_TIME - self._TIME_FOR_JOLLY,
                     3,  self.jolly_GUI.destroy)

        self.main_button.configure(state='disabled')

        self.stable_element_builder()

        Thread(
            target=lambda: self.s.run(blocking=True), daemon=True).start()

    def show_ranking(self):

        self.main_button.configure(text="Save data", command=self.save_data)
        self.arbiter_GUI.destroy()
        self.stable_element_builder()
        self.update_entry()

    def save_data(self):

        try:

            asksaveasfile(mode='w', defaultextension=".txt", filetypes=[("Text files", "*.txt")], parent=self).write(
                str(self._recorder))

        except Exception:

            showwarning(
                "Error",
                "An error occurred saving data, data will be copied it to the clipbord.",
            )

            run('clip', universal_newlines=True,
                input=str(self._recorder))

    # metods about wiget

    def generate_clock(self):
        """
        Generate the clock label
        """
        self.timer_label.configure(
            text=f"Time left: {self._timer_seconds // 3600:02d}: {(self._timer_seconds % 3600) // 60:02d}: {self._timer_seconds % 60:02d}"
        )

    def stable_element_builder(self):
        """
        Generate canvas whit scrollbar for ranking
        """

        # Creazione delle etichette per ogni domanda e riga
        for column in self._NUMBER_OF_QUESTIONS_RANGE_1:

            Label(self.frame_point, text=f"{column}", width=6).grid(
                column=column+1, row=0
            )

            Entry(self.frame_point, width=6, bd=5,
                  textvariable=self.stringvar_question[column], state='readonly', readonlybackground='white').grid(column=column+1, row=1)

        for row in range(len(self.NAMES_TEAMS)):

            Label(self.frame_point, anchor='e', textvariable=self.stringvar_start_row[row][0]).grid(
                column=0, row=row+2)

            Entry(self.frame_point, width=6, bd=5,
                  textvariable=self.stringvar_start_row[row][1], state='readonly', readonlybackground='white').grid(column=1, row=row+2)

            for column in self._NUMBER_OF_QUESTIONS_RANGE_1:

                self.entry_quetion_x_team[row][column].configure(
                    textvariable=self.stringvar_question_x_team[row][column])
                self.entry_quetion_x_team[row][column].grid(
                    column=column+1, row=row+2)

    def update_entry(self):
        """
        Update ranking
        """

        # Create value labels for each question
        for question in self._NUMBER_OF_QUESTIONS_RANGE_1:

            self.stringvar_question[question].set(
                self.point_answer(question))

        # Populate team points and color-code entries
        for row, team in enumerate(sorted(self.NAMES_TEAMS,
                                          key=lambda team: self.total_team_point(
                                              team), reverse=True)):

            self.stringvar_start_row[row][0].set(team)

            self.stringvar_start_row[row][1].set(self.total_team_point(team))

            for question in self._NUMBER_OF_QUESTIONS_RANGE_1:

                points = self.point_answer_x_squad(team, question)

                self.stringvar_question_x_team[row][question].set(
                    self.point_answer_x_squad(team, question))

                self.entry_quetion_x_team[row][question].config(
                    readonlybackground='red' if points < 0 else 'green' if points > 0 else 'white', fg='blue' if self._list_point[team][question][2] == 2 else 'black')

    # methods to submit answer or jolly

    def submit_answer(self, selected_team: str, entered_question: int, entered_answer: int):
        """
        The metod to submit an answer
        """

        # if is unanswered
        if self._list_point[selected_team][entered_question][1] == 0:

            # if correct
            if entered_answer == self._solutions[entered_question][0]:

                self._list_point[selected_team][entered_question][1] = 1

                self._list_point[selected_team][entered_question][3] = self._BONUS_ANSWER[min(
                    self._solutions[entered_question][1], self._N_BONUS_ANSWER)]

                self._solutions[entered_question][1] += 1

                # give bonus
                if (
                    sum(
                        [
                            team[1]
                            for team in self._list_point[selected_team][1:]
                        ]
                    )
                    == self._NUMBER_OF_QUESTIONS
                ):

                    self._list_point[selected_team][0] += self._BONUS_FULLED[min(
                        self._fulled, self._N_BONUS_FULLED)]
                    self._fulled += 1

            # if wrong
            else:
                self._list_point[selected_team][entered_question][0] += 1
                self._solutions[entered_question][2] += (
                    1
                    if self._list_point[selected_team][entered_question][0]
                    == 1
                    else 0
                )

        self._recorder.record_answer(
            selected_team, entered_question, entered_answer)

    def submit_jolly(self, selected_team: str, entered_question: int):
        """
        the metod to submit a jolly
        """
        # check timer staus and if other jolly are already been given
        self._list_point[selected_team][1][2] = 1

        if self._timer_seconds > (self._TOTAL_TIME - 600) and (
            sum(
                [
                    question[2]
                    for question in self._list_point[selected_team][1:]
                ]
            )
            == self._NUMBER_OF_QUESTIONS
        ):
            # adding jolly
            self._list_point[selected_team][entered_question][2] = 2
            self._recorder.record_jolly(selected_team, entered_question)

    # methods to calculate points

    def point_answer(self, question: int) -> int:
        """
        Return the value of answer
        """
        return int(self._solutions[question][3] + self._solutions[question][2] * 2)

    def point_answer_x_squad(self, team: str, question:  int) -> int:
        """
        Return the points made a team in a question
        """

        return (
            self._list_point[team][question][1] * self.point_answer(question)
            - self._list_point[team][question][0] * 10
            + self._list_point[team][question][3]
        ) * self._list_point[team][question][2]

    def total_team_point(self, team: str) -> int:
        """
        Return the point of a team
        """
        return sum(self.point_answer_x_squad(team, question)
                   for question in self._NUMBER_OF_QUESTIONS_RANGE_1
                   ) + self._list_point[team][0]


class Jolly_GUI(Toplevel):
    def __init__(self, main: Main):

        super().__init__(main)

        self.submit_method_main = main.submit_jolly

        self.title("Jolly")
        self.geometry("250x200")
        self.resizable(False, False)
        set_icon(self)

        # creatition entry for team
        Label(self, text="Team:").grid(row=0)

        self.team_var = StringVar(value="")
        Combobox(
            self,
            textvariable=self.team_var,
            values=main.NAMES_TEAMS,
            state='readonly',
        ).grid(row=1)

        Label(self, text="Question number:").grid(row=2)

        self.question_var = IntVar(value="")
        Entry(self, textvariable=self.question_var).grid(row=3)

        Button(self, text="Submit", command=self.submit_method).grid(
            row=6, pady=15)

        self.bind('<Return>', lambda key: self.submit_method())

        self.protocol('WM_DELETE_WINDOW', lambda: None)

    def submit_method(self):
        """
        The method associated to the button
        """
        try:
            Thread(
                target=self.submit_method_main(
                    self.team_var.get(), self.question_var.get())
            ).start()

        except TclError:
            pass

        finally:

            self.team_var.set("")
            self.question_var.set("")


class Arbiter_GUI(Jolly_GUI):

    def __init__(self, main: Main):

        super().__init__(main)

        self.submit_method_main = main.submit_answer

        self.title("Arbiter")

        Label(self, text="Insert an answer:").grid(row=4)
        self.answer_var = IntVar(value="")
        Entry(
            self, textvariable=self.answer_var).grid(row=5)

    def submit_method(self):
        """
        The method associated to the button
        """
        try:

            Thread(
                target=self.submit_method_main(
                    self.team_var.get(),
                    self.question_var.get(),
                    self.answer_var.get(),
                )
            ).start()

        except TclError:
            pass

        finally:

            self.team_var.set("")
            self.question_var.set("")
            self.answer_var.set("")


if __name__ == "__main__":

    # from cProfile import run
    # run('Main()')

    Main().mainloop()
