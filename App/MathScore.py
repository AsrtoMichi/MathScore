#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GUI
import configparser
from typing import Union, Literal
from tkinter import Tk, Toplevel, Canvas, StringVar, Entry, Label
from tkinter.ttk import Frame, Button, Scrollbar, Combobox
from tkinter.filedialog import askopenfilename, asksaveasfile

# os
from threading import Thread

# .ini reading
from configparser import ConfigParser
from ast import literal_eval
from os.path import join, dirname, abspath, exists


# Gestion of errors:
#   Configuration errors 1:
#       10 No .ini file was given
#       11 Unable to load data
#       12 Error reading the configuration file
# 2 Conclusion during the competions

class Recorder:
    def __init__(self, names_teams: list, number_of_question_tuple: tuple, total_time: int, base_points: int, base_value_question: int):
        self._jolly = {name: None for name in names_teams}
        self._answer = {name: []
                        for name in names_teams}
        self._values_questions = {question: [
            (total_time, base_value_question)] for question in number_of_question_tuple}
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
        return str((self._jolly, self._answer, self._values_questions, self._total_teams))


class Main(Tk):

    """
    That class is the main window: here are showed poits
    """

    def __init__(self):

        ini_file_path = abspath(join(dirname(__file__), 'Config.ini'))
        if not exists(ini_file_path):

            ini_file_path = askopenfilename(
                filetypes=[("Configuration files", "*.ini")])

            if ini_file_path == "":

                from tkinter.messagebox import showerror
                showerror(
                    "Error", "No .ini file was given.")
                exit(10)

        try:
            open(ini_file_path, "r")

        except (FileNotFoundError, IOError, PermissionError):
            from tkinter.messagebox import showerror
            showerror(
                "Error", "Unable to find or read the config.ini file")
            exit(11)

        else:

            config = ConfigParser()
            config.read(ini_file_path)

        try:

            # teams' names
            self.NAMES_TEAMS = tuple(
                config.get('Teams', 'teams').split(', '))

            # genaration timer
            self._TOTAL_TIME = self._timer_seconds = config.getint(
                'Timer', 'time')*60

            self._TIME_FOR_JOLLY = config.getint('Timer', 'time_for_jolly')*60

            # setting DERIVE
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

            self._NUMBER_OF_QUESTIONS_RANGE = range(
                1, self._NUMBER_OF_QUESTIONS+1)

            # 0: errors
            # 1: status
            # 2: jolly
            # 3: bonus

            # list point, bonus, n_fulled

            self._list_point = {
                name: [self._NUMBER_OF_QUESTIONS * 10] + [[0, 0, 1, 0]
                                                          for _ in self._NUMBER_OF_QUESTIONS_RANGE] for name in self.NAMES_TEAMS}

            self._fulled = 0

            self._recorder = Recorder(
                self.NAMES_TEAMS, self._NUMBER_OF_QUESTIONS_RANGE, self._TOTAL_TIME, self._NUMBER_OF_QUESTIONS * 10, value)

        except configparser.NoSectionError:

            from tkinter.messagebox import showerror
            showerror(
                "Error", f"An error orccured reading the config.ini file")
            exit(12)

        else:

            # creation Main window and castomization
            super().__init__()
            self.title("Competitors")
            self.geometry('1850x630')
            self.resizable(True, False)

            try:
                self.iconbitmap(
                    abspath(join(dirname(__file__), 'MathScore.ico')))
            except (FileNotFoundError, IOError, PermissionError):
                pass

            # widget costruction
            self.timer_label = Label(self, font=('Helvetica', 18, 'bold'))
            self.timer_label.pack()
            self.generate_clock()

            self.main_button = Button(
                self, text="Start", command=self.start_competition)
            self.main_button.pack()

            points_label = Frame(self, width=1800, height=600)
            points_label.pack()

            # Creazione del canvas all'interno dell'etichetta dei punti
            canvas = Canvas(
                points_label,
                width=1800,
                height=600,
                scrollregion=(0, 0, 1800, len(self.NAMES_TEAMS) * 26),
            )
            canvas.pack(side='left', expand=True, fill='both')

            # Aggiunta di una barra di scorrimento verticale
            scrollbar = Scrollbar(points_label, command=canvas.yview)
            scrollbar.pack(side='right', fill='y')

            canvas.configure(yscrollcommand=scrollbar.set)

            self.frame_point = Frame(
                canvas, width=1800, height=len(self.NAMES_TEAMS) * 26)
            canvas.create_window((0, 0), window=self.frame_point, anchor='nw')

            self.protocol('WM_DELETE_WINDOW', lambda: exit(2 if self._timer_seconds !=
                                                           0 else 0))

    def run(self):

        Thread(target=self.update_main()).start()

        if self._timer_seconds > 0:
            self.after(1000, self.run)
        else:
            self.main_button.configure(
                state='normal', text="Show ranking", command=self.show_ranking)
            self.timer_label.destroy()

    def update_main(self):

        self._timer_seconds -= 1
        self.generate_clock()

        # update points each minut
        if self._timer_seconds % 60 == 0 and self._timer_seconds >= 1200:
            for question in self._NUMBER_OF_QUESTIONS_RANGE:
                if self._solutions[question][1] < self._DERIVE:
                    self._solutions[question][3] += 1

        if self._timer_seconds > 30:
            self.update_entry()

        if self._timer_seconds == (self._TOTAL_TIME - self._TIME_FOR_JOLLY):
            self.jolly_GUI.destroy()

        remove point label befor the end
        if self._timer_seconds == 30:

            # Clear all widgets in the frame except protected columns
            for widget in self.frame_point.winfo_children():
                widget.destroy()

        for team in self.NAMES_TEAMS:
            self._recorder.record_total_teams(
                team, self._timer_seconds, self.total_team_point(team))

        for question in self._NUMBER_OF_QUESTIONS_RANGE:
            self._recorder.record_values_questions(
                question, self._timer_seconds, self.point_answer(question))

        # methods about the progress ot time

    def start_competition(self):
        """
        Initialise the timer and block start buttom
        """
        self.arbiter_GUI = Arbiter_GUI(self)
        self.jolly_GUI = Jolly_GUI(self)

        self.main_button.configure(state='disabled')

        self.stable_element_builder()

        self.run()

    def show_ranking(self):

        self.main_button.configure(state='disabled')

        try:

            asksaveasfile(mode='w', defaultextension=".txt", filetypes=[("Text files", "*.txt")], parent=self).write(
                str(self._recorder))

        except Exception:

            from tkinter.messagebox import showerror
            from subprocess import run

            showerror(
                "Error",
                f"An error occurred saving data, data will be copied it to the clipbord.",
            )

            run('clip', universal_newlines=True,
                input=str(self._recorder))

        self.arbiter_GUI.destroy()
        self.stable_element_builder()
        self.update_entry()

    # metods about wiget

    def generate_clock(self):
        """
        Generate the clock label
        """
        self.timer_label.configure(
            text=f"Time left: {self._timer_seconds // 3600: 02}: {(self._timer_seconds % 3600) // 60: 02}: {self._timer_seconds % 60: 02}"
        )

    def stable_element_builder(self):
        """
        Generate canvas whit scrollbar for ranking
        """

        # Creazione delle etichette per ogni domanda e riga
        for question in self._NUMBER_OF_QUESTIONS_RANGE:
            Label(self.frame_point, text=f"{question}", width=6).grid(
                column=question+1, row=0
            )

    def update_entry(self):
        """
        Update ranking
        """

        # Clear all widgets in the frame except protected columns
        for widget in self.frame_point.winfo_children():
            if widget.grid_info()['row'] != 0:
                widget.destroy()

        # Create value labels for each question
        for question in self._NUMBER_OF_QUESTIONS_RANGE:
            value_label = Entry(self.frame_point, width=6, bd=5)
            value_label.insert(0, str(self.point_answer(question)))
            value_label.grid(column=question + 1, row=1)

        # Populate team points and color-code entries
        for row, frame in enumerate(
            sorted(
                [(self.total_team_point(team), team)
                 for team in self.NAMES_TEAMS],
                key=lambda x: x[0],
                reverse=True,
            ),
            2,
        ):
            team = frame[1]

            Label(self.frame_point, text=f"{team}: ", anchor='e').grid(
                column=0, row=row
            )

            total_num = Entry(self.frame_point, width=6, bd=5)
            total_num.insert(0, str(self.total_team_point(team)))
            total_num.grid(column=1, row=row)

            for column in self._NUMBER_OF_QUESTIONS_RANGE:

                points = self.point_answer_x_squad(team, column)

                total_num = Entry(self.frame_point, width=6, bd=5,
                                  bg='red' if points < 0 else 'green' if points > 0 else 'white')
                total_num.insert(
                    0, self.point_answer_x_squad(team, column, True))
                total_num.grid(column=column + 1, row=row)

    # methods to submit answer

    def submit_answer(
        self, selected_team: str, entered_question: int, entered_answer: int
    ):
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

    def point_answer_x_squad(
        self, team: str, question: Union[Literal['base'], int], jolly_simbol: bool = False
    ) -> Union[int, str]:
        """
        Return the points made a team in a question
        """
        answer_point = self._list_point[team][question]

        # Calculate the output points
        result = (
            answer_point[1] * self.point_answer(question)
            - answer_point[0] * 10
            + answer_point[3]
        ) * answer_point[2]

        return (
            f"{result} J"
            if answer_point[2] == 2 and jolly_simbol
            else result
        )

    def total_team_point(self, team: str) -> int:
        """
        Return the point of a team
        """
        return sum(self.point_answer_x_squad(team, question)
                   for question in self._NUMBER_OF_QUESTIONS_RANGE
                   ) + self._list_point[team][0]


class Arbiter_GUI(Toplevel):
    def __init__(self, main: Main):
        super().__init__(main)

        self.submit_answer_main = main.submit_answer

        # starting artiter's window
        self.title("Arbiter")
        self.geometry("500x210")
        self.resizable(False, False)
        self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

        # craation entry for data
        Label(self, text="Team:").pack()
        self.selected_team = StringVar(value="")
        self.squadre_entry = Combobox(
            self,
            textvariable=self.selected_team,
            values=main.NAMES_TEAMS,
            state='readonly',
        )
        self.squadre_entry.pack()

        Label(self, text="Question number:").pack()
        self.question_entry = Entry(self)
        self.question_entry.pack()

        Label(self, text="Insert an answer:").pack()
        self.answer_entry = Entry(self)
        self.answer_entry.pack()

        Button(self, text="Submit", command=self.submit_answer).pack(pady=15)

        self.bind('<Return>', self.submit_answer)

    def submit_answer(self, event: str = None):
        """
        The method associated to the button
        """
        try:

            Thread(
                target=self.submit_answer_main(
                    self.selected_team.get(),
                    int(self.question_entry.get()),
                    int(self.answer_entry.get()),
                )
            ).start

        except ValueError:
            pass

        finally:

            self.selected_team.set("")
            self.question_entry.delete(0, "end")
            self.answer_entry.delete(0, "end")


class Jolly_GUI(Toplevel):
    def __init__(self, main: Main):
        super().__init__(main)

        self.submit_jolly_main = main.submit_jolly

        # starting jolly window
        self.title("Jolly")
        self.geometry("500x160")
        self.resizable(False, False)
        self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

        # creatition entry for team
        Label(self, text="Team:").pack()
        self.selected_team_jolly = StringVar(value="")
        self.squadre_entry_jolly = Combobox(
            self,
            textvariable=self.selected_team_jolly,
            values=main.NAMES_TEAMS,
            state='readonly',
        )
        self.squadre_entry_jolly.pack()

        # creatition entry for question
        Label(self, text="Question number:").pack()
        self.question_entry_jolly = Entry(self)
        self.question_entry_jolly.pack()

        Button(self, text="Submit", command=self.submit_jolly).pack(pady=15)

        self.bind('<Return>', self.submit_jolly)

    def submit_jolly(self, event: str = None):
        """
        The method associated to the button
        """
        try:
            Thread(
                target=self.submit_jolly_main(
                    self.selected_team_jolly.get(), int(self.question_entry_jolly.get())
                )
            ).start

        except ValueError:
            pass

        finally:
            self.selected_team_jolly.set("")
            self.question_entry_jolly.delete(0, "end")


if __name__ == "__main__":

    # from cProfile import run
    # run('Main()')

    Main().mainloop()
