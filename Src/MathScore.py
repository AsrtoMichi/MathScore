#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# Mathscore
This app is aimed at counting points in math competitions.
The app consists of two windows: one for viewing the scores, one for entering answers and jolly (only one for team).
It also saves all anser and jolly in a .txt file, to make grafic.
"""


__author__ = "Michele Gallo", "https://github.com/AsrtoMichi"
__version__ = "1.0.0.0"
__suorce_code__ = "https://github.com/AsrtoMichi/MathScore"
__license__ = "https://raw.githubusercontent.com/AsrtoMichi/MathScore/main/LICENSE"

__credits__ = """
Sandro Campigotto, the creator of  PHI Quadro
Alessandro Chiozza, Federico Micelli and Giorgio Sorgente, for technical help
"""

# GUI
from tkinter import Tk, Toplevel, Canvas, Entry, Label, Variable
from tkinter.ttk import Frame, Button, Scrollbar, Combobox
from tkinter.filedialog import askopenfilename, asksaveasfile
from tkinter.messagebox import askokcancel, showerror, showwarning

# OS
from sys import exit as sys_exit
# sys_exit is used to prevent problem in the exe version

# .ini reading
from configparser import ConfigParser, ParsingError
from ast import literal_eval
from os import access, stat

# decoration
from typing import Iterable


def join(file_name):
    sep = '/'if '/' in __file__ else '\\'
    return __file__[:__file__.rfind(sep) + 1] + sep + file_name


class Recorder:

    """
    This class is used for save:
    - answer given by a team
    - jolly chosen for a team
    """

    def __init__(self,  names_teams: Iterable[str]):

        self._jolly = {name: None for name in names_teams}
        self._answer = {name: [] for name in names_teams}

    def record_jolly(self, name_team: str, time: int, question: int):
        """
        Record a jolly
        """
        self._jolly[name_team] = (time, question)

    def record_answer(self, name_team: str, time: int, question: int, answer: int):
        """
        Record an answer
        """
        self._answer[name_team].append((time, question, answer))

    def __str__(self):

        return str(self._jolly, self._answer)


class StringVar(Variable):
    """Value holder for strings variables."""

    def __init__(self, master):
        """Construct a string variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to "")
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        Variable.__init__(self, master)

    def set(self, value=""):
        """Set the variable to VALUE."""
        self._tk.globalsetvar(self._name, value)

    def get(self) -> str:
        """Return value of variable as string."""
        return self._tk.globalgetvar(self._name)


class IntVar(Variable):
    """Value holder for integer variables."""

    def __init__(self, master):
        """Construct an integer variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to 0)
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        Variable.__init__(self, master)

    def set(self, value=""):
        """Set the variable to VALUE."""
        self._tk.globalsetvar(self._name, value)

    def get(self) -> int:
        """Return the value of the variable as an integer."""
        try:
            return int(self._tk.globalgetvar(self._name))
        except ValueError:
            return


class Main(Tk):

    """
    Is the main window: here are showed poits
    """

    def __init__(self):
        """
        Step of init method:

        0. creation of the main Window:

        1. Individuate the .ini file:
            1. in the same directory
            2. ask to the user
            Error exit code: 10 "No .ini file has been give." 

        2. check if the config.ini exists/possibly open it:
            Error exit code: 11 "Impossible to read the config.ini file."

        3. reading of file using ConfigParser:
            - extracted data are (variable, section in .ini):
            - self.NAMES_TEAMS ['Generic']['teams']
            - (name competition) config['Generic']['name_competion']
            - self._TOTAL_TIME, self._timer_seconds ['Timer']['time']
            - self._TIME_FOR_JOLLY['Timer']['time_for_jolly']
            - self._DERIVE ['Points']['derive']
            - self._BONUS_ANSWER ['Points']['bonus_answer']
            - self._BONUS_FULLED ['Points']['bonus_fulled']
            - value ['Points']['vantage']
            - solutions ['Solutions']['solutions']

            Error exit code: KeyError, ValueError, ParsingError ValueError 12 
                "An error occurred reading the config.ini file"

        Error exit code: Configuration not completed 1 
            "Impossible to find or read the config.ini file."

        4. - creation of ArbiterGUI
           - the creation of a timer label
           - the creation of the main button
           - the creation of a scrollable area for the point's grid

        5. - creation of the list of IntVar e StringVar ad Entry to show points
           - connctio var to entry
           - griding entry

        6. modification of WM_DELETE_WINDOW to prevent accidental closures:
            Error code 2 if the windows are closed during the competition
        """

        # creation Main window and castomization
        super().__init__()
        self.tk.call('wm', 'resizable', self._w, False, False)

        try:
            self.tk.call('wm', 'iconbitmap', self._w, '-default',
                         join('MathScore.ico'))
        except (FileNotFoundError, OSError, PermissionError):
            pass

        ini_file_path = join('Config.ini')
        # serch the ini file in the same directory

        try:
            stat(ini_file_path)
        except OSError:
            # if ther isn't the ini file in the same path ask to the user to select the file
            ini_file_path = askopenfilename(
                parent=self,
                filetypes=[("Configuration files", "*.ini")])

            if ini_file_path == "":

                showerror(
                    "Error", "No .ini file has been give.", master=self)
                sys_exit(10)

        if not access(ini_file_path, 4):
            showerror(
                "Error", "Impossible to read the config.ini file.", master=self)
            sys_exit(11)

        try:
            config = ConfigParser()
            config.read(ini_file_path)

            self.NAMES_TEAMS = tuple(config['Generic']['teams'].split(', '))

            self._timer_seconds, self._TIME_FOR_JOLLY = int(
                config['Timer']['time'])*60, int(config['Timer']['time_for_jolly'])*60

            # DERIVE is the minum number of question to block the grow of the value of a question
            self._DERIVE = int(config['Points']['derive'])

            self._BONUS_ANSWER = literal_eval(
                config['Points']['bonus_answer'])
            self._N_BONUS_ANSWER = len(self._BONUS_ANSWER)

            for bonus in self._BONUS_ANSWER:
                assert isinstance(bonus, int)

            self._BONUS_FULLED = literal_eval(
                config['Points']['bonus_fulled'])
            self._N_BONUS_FULLED = len(self._BONUS_FULLED)

            for bonus in self._BONUS_FULLED:
                assert isinstance(bonus, int)

            # 0: solution
            # 1: correct
            # 2: incorrect
            # 3: value

            value = int(config['Points']['vantage'])

            solutions = literal_eval(config['Solutions']['solutions'])

            for solution in solutions:
                assert isinstance(solution, int)

            self._solutions = [0] + [
                [solution,  0,  0, value]
                for solution in solutions
            ]

            self._NUMBER_OF_QUESTIONS = len(solutions)

            self._NUMBER_OF_QUESTIONS_RANGE_1 = range(
                1, self._NUMBER_OF_QUESTIONS+1)

            # 0: errors
            # 1: status
            # 2: jolly
            # 3: bonus

            self._list_point = {
                name: [self._NUMBER_OF_QUESTIONS * 10] + [[0]*4
                                                          for _ in self._NUMBER_OF_QUESTIONS_RANGE_1
                                                          ] for name in self.NAMES_TEAMS}

            self._recorder = Recorder(
                self.NAMES_TEAMS)

        except (KeyError, ValueError, ParsingError, TypeError, AssertionError):
            showerror(
                "Error", "An error occurred reading the config.ini file", master=self)
            sys_exit(12)

        except:
            showerror(
                "Error", "Impossible to find or read the config.ini file.", master=self)
            sys_exit(1)

        else:
            self.tk.call('wm', 'title', self._w,
                         config['Generic']['name_competion'])

            self.arbiterGUI = ArbiterGUI(self)

            # widget costruction
            self.timer_label = Label(self, font=('Helvetica', 18, 'bold'),
                                     text=f"Time left: {self._timer_seconds // 3600:02d}:{(self._timer_seconds % 3600) // 60:02d}:00")
            self.timer_label.pack()

            self.main_button = Button(
                self, text="Start", command=self.start_competition)
            self.main_button.pack()

            # cration of scrollabe area
            self.points_label = Frame(self, width=1625, height=600)

            canvas = Canvas(
                self.points_label,
                width=1625,
                height=600,
                scrollregion=(0, 0, 1625, len(self.NAMES_TEAMS) * 26),
            )
            canvas.pack(side='left', expand=True, fill='both')

            scrollbar = Scrollbar(self.points_label, command=canvas.yview)
            scrollbar.pack(side='right', fill='y')

            canvas.configure(yscrollcommand=scrollbar.set)

            frame_point = Frame(
                canvas, width=1625, height=len(self.NAMES_TEAMS) * 26)
            canvas.create_window((0, 0), window=frame_point, anchor='nw')

            self.var_head_col = [None] + [IntVar(self)
                                          for _ in self._NUMBER_OF_QUESTIONS_RANGE_1]

            for column in self._NUMBER_OF_QUESTIONS_RANGE_1:

                Label(frame_point, text=column, width=6).grid(
                    column=column+1, row=0
                )

                Entry(frame_point, width=6, bd=5,
                      textvariable=self.var_head_col[column], state='readonly',
                      readonlybackground='white').grid(column=column+1, row=1)

            self.var_head_row = [
                [StringVar(self), IntVar(self)] for _ in self.NAMES_TEAMS]

            self.var_question_x_team = [
                [None] + [IntVar(self)
                          for _ in self._NUMBER_OF_QUESTIONS_RANGE_1]
                for _ in self.NAMES_TEAMS]

            self.entry_question_x_team = [
                [None] + [Entry(frame_point, width=6, bd=5,
                                state='readonly', readonlybackground='white',
                                textvariable=intvar)
                          for intvar in row[1:]]
                for row in self.var_question_x_team]

            for row in range(len(self.NAMES_TEAMS)):

                Label(frame_point, anchor='e', textvariable=self.var_head_row[row][0]).grid(
                    column=0, row=row+2)

                Entry(frame_point, width=6, bd=5,
                      textvariable=self.var_head_row[row][1],
                      state='readonly', readonlybackground='white').grid(column=1, row=row+2)

                for column in self._NUMBER_OF_QUESTIONS_RANGE_1:

                    self.entry_question_x_team[row][column].grid(
                        column=column+1, row=row+2)

            self.update_entry()

            self.wm_protocol('WM_DELETE_WINDOW',
                             lambda: sys_exit(2)
                             if askokcancel("Closing confirm", "All data can be losted.", master=self)
                             else None)

    # method about runtime

    def update_values_questions(self):
        """
        Update the values of questions of 1 if the number of answers is less than the derive
        """
        for question in self._solutions[1:]:
            question[3] += 1 if question[1] < self._DERIVE else None

        self.update_entry()

    # methods about the progress ot time

    def start_competition(self):
        """
        Programming of the scheduler:
            - TOTAL TIME - 30: elimination point's grid
            - TOTAL TIME: elimination of timer label, reconfiguration of main button
            - 1 to TOTAL TIME: update the timer
            - Each minute until self._TOTAL_TIME - 1200: update questions' value
            - TIME FOR JOLLY: remove the possibility of giving jolly, assignation jolly at number 1 if possible

        Allow to give answers and jolly
        Show points
        """
        TOTAL_TIME = self._timer_seconds

        self.points_label.pack()

        for time in range(1000, (TOTAL_TIME*1000)+1, 1000):
            self.after(time, self.update_timer)

        for time in range(60000, (TOTAL_TIME - 1200)*1000, 60000):
            self.after(time, self.update_values_questions)

        self.main_button.configure(state='disabled')
        self.arbiterGUI.jolly_button.configure(state='normal')
        self.arbiterGUI.answer_button.configure(state='normal')

        self.after(self._TIME_FOR_JOLLY * 1000,
                   self.arbiterGUI.jolly_button.configure, {'state': 'disabled'})
        self.after(self._TIME_FOR_JOLLY * 1000,
                   lambda: [self.submit_jolly(team, 1) for team in self.NAMES_TEAMS])

        self.after((TOTAL_TIME - 30)*1000, self.points_label.pack_forget)

        self.after(TOTAL_TIME*1000, self.main_button.configure,
                   {'state': 'normal', 'text': "Show ranking", 'command': self.show_ranking})
        self.after(TOTAL_TIME*1000, self.timer_label.destroy)

    def show_ranking(self):
        """
        Show the final ranking and configure the main button to save data
        """

        self.main_button.configure(
            text="Save data", command=self.save_data)
        self.points_label.pack()
        self.arbiterGUI.destroy()
        self.wm_protocol('WM_DELETE_WINDOW',
                         lambda: sys_exit(0)
                         if askokcancel("Closing confirm", "All data can be losted.", master=self)
                         else None)

    def save_data(self):
        """
        Try to save data if is not possible copy them in clipboard
        """

        try:

            asksaveasfile(master=self,
                          title="Save data",
                          filetypes=[("Text files", "*.txt")]
                          ).write(str(self._recorder))

        except AttributeError:
            showwarning(
                "Error",
                "Data not saved",
                master=self
            )

        except (OSError, PermissionError):

            showwarning(
                "Error",
                "An error occurred saving data, data will be copied it to the clipbord.",
                master=self
            )

            self.clipboard_append(str(self._recorder))

    # metods about wiget

    def update_timer(self):
        """
        Generate the clock label
        """
        self._timer_seconds -= 1
        self.timer_label.configure(
            text=f"Time left: {self._timer_seconds // 3600:02d}:{(self._timer_seconds % 3600) // 60:02d}:{self._timer_seconds % 60:02d}"
        )

    def update_entry(self):
        """
        Update values in points
        """

        # Create value labels for each question
        for question in self._NUMBER_OF_QUESTIONS_RANGE_1:

            self.var_head_col[question].set(
                self.value_question(question))

        # Populate team points and color-code entries
        for row, team in enumerate(sorted(self.NAMES_TEAMS,
                                          key=self.total_points_team,
                                          reverse=True)):

            self.var_head_row[row][0].set(team)

            self.var_head_row[row][1].set(self.total_points_team(team))

            for question in self._NUMBER_OF_QUESTIONS_RANGE_1:

                points = self.value_question_x_squad(team, question)

                self.var_question_x_team[row][question].set(
                    self.value_question_x_squad(team, question))

                self.entry_question_x_team[row][question].configure(
                    readonlybackground='red' if points < 0 else 'green' if points > 0 else 'white',
                    fg='blue' if self._list_point[team][question][2] else 'black',
                    font=('Helvetica', 9, 'bold')
                    if self._list_point[team][question][2] else (
                        'Helvetica', 9, 'normal'))

    # methods to submit answer or jolly

    def submit_answer(self, selected_team: str, entered_question: int, entered_answer: int):
        """
        The mehtod to submit answers
        """

        if entered_question in self._NUMBER_OF_QUESTIONS_RANGE_1:

            data_point_team = self._list_point[selected_team][entered_question]
            data_question = self._solutions[entered_question]

            # if is unanswered
            if not data_point_team[1]:

                # if correct
                if entered_answer == data_question[0]:

                    data_point_team[1] = 1

                    data_point_team[3] = self._BONUS_ANSWER[min(
                        data_question[1], self._N_BONUS_ANSWER)]

                    data_question[1] += 1

                    # give bonus
                    if sum(question[1]
                            for question in self._list_point[selected_team][1:]
                           ) == self._NUMBER_OF_QUESTIONS:

                        self._list_point[selected_team][0] += self._BONUS_FULLED[min(
                            self._solutions[0], self._N_BONUS_FULLED)]
                        self._solutions[0] += 1

                # if wrong
                else:
                    data_point_team[0] += 1
                    data_question[2] += 1 if data_point_team[0] else 0

            self._recorder.record_answer(
                selected_team, self._timer_seconds, entered_question, entered_answer)

            self.update_entry()

    def submit_jolly(self, selected_team: str, entered_question: int):
        """
        The method to submit jolly

        """

        if entered_question in self._NUMBER_OF_QUESTIONS_RANGE_1 and sum(question[2]
                                                                         for question in self._list_point[selected_team][1:]
                                                                         ) == 0:

            # adding jolly
            self._list_point[selected_team][entered_question][2] = 1
            self._recorder.record_jolly(
                selected_team, self._timer_seconds, entered_question)

            self.update_entry()

    # methods to calculate points

    def value_question(self, question: int) -> int:
        """
        Return the value of answer
        """
        return int(self._solutions[question][3] + self._solutions[question][2] * 2)

    def value_question_x_squad(self, team: str, question:  int) -> int:
        """
        Return the points made by a team in a question
        """

        list_point_team = self._list_point[team][question]

        return (
            list_point_team[1] * self.value_question(question)
            - list_point_team[0] * 10
            + list_point_team[3]
        ) * (list_point_team[2] + 1)

    def total_points_team(self, team: str) -> int:
        """
        Return the points of a team
        """
        return sum(self.value_question_x_squad(team, question)
                   for question in self._NUMBER_OF_QUESTIONS_RANGE_1
                   ) + self._list_point[team][0]


class ArbiterGUI(Toplevel):
    """
    The window to submit jolly and answers
    """

    def __init__(self, main: Main):

        super().__init__(main)

        self.submit_jolly_main = main.submit_jolly
        self.submit_answer_main = main.submit_answer

        self.tk.call('wm', 'title', self._w, 'Arbiter')
        self.tk.call('wm', 'geometry', self._w, '250x250')
        self.tk.call('wm', 'resizable', self._w, False, False)

        Label(self, text="Team:").pack()
        self.team_var = StringVar(self)
        Combobox(
            self,
            textvariable=self.team_var,
            values=main.NAMES_TEAMS,
            state='readonly'
        ).pack()

        Label(self, text="Question number:").pack()
        self.question_var = IntVar(self)
        Entry(self, textvariable=self.question_var).pack()

        Label(self, text="Answer:").pack()
        self.answer_var = IntVar(self)
        Entry(self, textvariable=self.answer_var).pack()

        self.jolly_button = Button(
            self, text="Submit Jolly", command=self.submit_jolly, state='disabled')
        self.jolly_button.pack(pady=15)

        self.answer_button = Button(
            self, text="Submit Answer", command=self.submit_answer, state='disabled')
        self.answer_button.pack()

        self.protocol('WM_DELETE_WINDOW', lambda: None)

    def submit_jolly(self):
        """
        The method associated to the button
        """
        self.submit_jolly_main(
            self.team_var.get(),
            self.question_var.get())

        self.clean()

    def submit_answer(self):
        """
        The method associated to the button
        """

        self.submit_answer_main(
            self.team_var.get(),
            self.question_var.get(),
            self.answer_var.get())

        self.clean()

    def clean(self):
        """
        Reset value of IntVar and StringVar
        """
        self.team_var.set()
        self.question_var.set()
        self.answer_var.set()


if __name__ == "__main__":

    # from cProfile import run
    # run('Main()')

    Main().mainloop()
