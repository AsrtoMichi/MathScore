#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# Mathscore
This app is aimed at counting points in math competitions.
The app consists of three windows: one for viewing the scores, one for entering the results
and one for entering the jolly (only one for team).
It also saves all variations of the total points and saves that in a .txt file, to make grafic.

## Credit
This app is app is inspired by PHI Quadro.
"""

# GUI
from tkinter import Tk, Toplevel, Canvas, Entry, Label, Variable
from tkinter.ttk import Frame, Button, Scrollbar, Combobox
from tkinter.filedialog import askopenfilename, asksaveasfile
from tkinter.messagebox import askokcancel, showerror, showwarning

# OS
from sys import exit as sys_exit
# sys_exit is used to prevent problem exe version

# .ini reading
from configparser import ConfigParser, ParsingError
from ast import literal_eval
from os.path import join, dirname, abspath, exists
from os import access

# decoration
from typing import Dict, List, Callable


def set_icon(window: Tk | Toplevel):
    """
    Set the icon of windows
    """
    try:
        window.iconbitmap(abspath(join(dirname(__file__), 'MathScore.ico')))
    except (FileNotFoundError, OSError, PermissionError):
        pass


class Recorder:

    """
    This class is used for save:
    - values of question in the time
    - tootal points of a team in the time
    - answer given by a team
    - jolly chosen for a team     
    """

    def __init__(self,  names_teams: List[str],
                 number_of_question_range_1: range,
                 total_time: int, base_points: int,
                 base_value_question: int,
                 clipboard_append: Callable):

        self._jolly = {name: None for name in names_teams}
        self._answer = {name: [] for name in names_teams}

        self._values_questions = [None] + [[
            (total_time, base_value_question)] for _ in number_of_question_range_1]

        self._total_teams = {name: [(total_time, base_points)]
                             for name in names_teams}

        self.clipboard_append = clipboard_append

    def record_jolly(self, name_team: str, question: int):
        """
        Record a jolly
        """
        self._jolly[name_team] = question

    def record_answer(self, name_team: str, time: int, answer: int):
        """
        Record an answer
        """
        self._answer[name_team].append((time, answer))

    def record_values_questions(self, question: int, time: int, value: int):
        """
        Record a value of a questio if is different from latest
        """
        if self._values_questions[question][-1][1] != value:
            self._values_questions[question].append((time, value))

    def record_total_teams(self, name_team: str, time: int, value: int):
        """
        Record the total topin of the tem if is different from latest
        """
        if self._total_teams[name_team][-1][1] != value:
            self._total_teams[name_team].append((time, value))

    def save(self):
        """
        Try to save data if is not possible copy them in clipboard
        """

        try:

            asksaveasfile(mode='w', defaultextension=".txt",
                          filetypes=[("Text files", "*.txt")], parent=self).write(
                (self._jolly, self._answer,
                 self._values_questions, self._total_teams,
                 self._values_questions[1][0][0]))

        except (OSError, FileNotFoundError, OSError):

            showwarning(
                "Error",
                "An error occurred saving data, data will be copied it to the clipbord.",
            )

            self.clipboard_append((self._jolly, self._answer,
                                   self._values_questions, self._total_teams,
                                   self._values_questions[1][0][0]))


class StringVar(Variable):
    """Value holder for strings variables."""
    _default = ""

    def __init__(self, master=None, value=None, name=None):
        """Construct a string variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to "")
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        Variable.__init__(self, master, value, name)

    def set(self, value=""):
        """Set the variable to VALUE."""
        return self._tk.globalsetvar(self._name, value)

    def get(self) -> str:
        """Return value of variable as string."""
        return self._tk.globalgetvar(self._name)


class IntVar(Variable):
    """Value holder for integer variables."""

    def __init__(self, master=None, value=None, name=None):
        """Construct an integer variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to 0)
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        Variable.__init__(self, master, value, name)

    def set(self, value=""):
        """Set the variable to VALUE."""
        return self._tk.globalsetvar(self._name, value)

    def get(self) -> int:
        """Return the value of the variable as an integer."""
        value = self._tk.globalgetvar(self._name)
        try:
            return int(value)
        except ValueError:
            return 0


class Main(Tk):

    """
    Is the main window: here are showed poits
    """

    def __init__(self):
        """
        Step of init method:

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

        4. creation of the main Window:
            - creation of ArbiterGUI
            - the creation of a timer label
            - the creation of the main button
            - the creation of a scrollable area for the point's grid

        5. creation of the list of IntVar e StringVar ad Entry to show points; 

        6. modification of WM_DELETE_WINDOW to prevent accidental closures:
            Error code 2 if the windows are closed during the competition
        """

        ini_file_path = abspath(join(dirname(__file__), 'Config.ini'))
        # serch the ini file in the same directory
        # abspath is use to prevent problem the exe conversion

        if not exists(ini_file_path):

            # if ther isn't the ini file in the same path ask to the user to select the file
            ini_file_path = askopenfilename(
                filetypes=[("Configuration files", "*.ini")])

            if ini_file_path == "":

                showerror(
                    "Error", "No .ini file has been give.")
                sys_exit(10)

        if not access(ini_file_path, 4):
            showerror(
                "Error", "Impossible to read the config.ini file.")
            sys_exit(11)

        try:
            config = ConfigParser()
            config.read(ini_file_path)

            self.NAMES_TEAMS = tuple(config['Generic']['teams'].split(', '))

            self._TOTAL_TIME = self._timer_seconds = int(
                config['Timer']['time'])*60

            self._TIME_FOR_JOLLY = int(config['Timer']['time_for_jolly'])*60

            # DERIVE is the minum number of question to block the grow of the value of a question
            self._DERIVE = int(config['Points']['derive'])

            self._BONUS_ANSWER = literal_eval(
                config['Points']['bonus_answer'])
            self._N_BONUS_ANSWER = len(self._BONUS_ANSWER)

            for bonus in self._BONUS_ANSWER:
                if not isinstance(bonus, int):
                    raise ValueError

            self._BONUS_FULLED = literal_eval(
                config['Points']['bonus_fulled'])
            self._N_BONUS_FULLED = len(self._BONUS_FULLED)

            for bonus in self._BONUS_FULLED:
                if not isinstance(bonus, int):
                    raise ValueError

            # 0: solution
            # 1: correct
            # 2: incorrect
            # 3: value

            value = int(config['Points']['vantage'])

            solutions = literal_eval(config['Solutions']['solutions'])

            for solution in solutions:
                if not isinstance(solution, int):
                    raise ValueError

            self._solutions: List[int, List[int]] = [0] + [
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

            # list point, bonus, n_fulled

            self._list_point: Dict[str, List[int, List[int]]] = {
                name: [self._NUMBER_OF_QUESTIONS * 10] + [[0, 0, 1, 0]
                                                          for _ in self._NUMBER_OF_QUESTIONS_RANGE_1
                                                          ] for name in self.NAMES_TEAMS}

            self._recorder = Recorder(
                self.NAMES_TEAMS,
                self._NUMBER_OF_QUESTIONS_RANGE_1,
                self._TOTAL_TIME,
                self._NUMBER_OF_QUESTIONS * 10,
                value, self.clipboard_append)

        except (KeyError, ValueError, ParsingError, TypeError):

            showerror(
                "Error", "An error occurred reading the config.ini file")
            sys_exit(12)

        except Exception:
            showerror(
                "Error", "Impossible to find or read the config.ini file.")
            sys_exit(1)

        else:

            # creation Main window and castomization
            super().__init__()

            self.tk.call('wm', 'title', self._w,
                         config['Generic']['name_competion'])
            self.tk.call('wm', 'geometry', self._w, '1600x630')
            self.tk.call('wm', 'resizable', self._w, False, False)
            set_icon(self)

            self.arbiterGUI = ArbiterGUI(self)

            # widget costruction
            self.timer_label = Label(self, font=('Helvetica', 18, 'bold'))
            self.timer_label.pack()
            self.generate_clock()

            self.main_button = Button(
                self, text="Start", command=self.start_competition)
            self.main_button.pack()

            # cration of scrollabe area
            points_label = Frame(self, width=1550, height=600)
            points_label.pack()

            canvas = Canvas(
                points_label,
                width=1550,
                height=600,
                scrollregion=(0, 0, 1550, len(self.NAMES_TEAMS) * 26),
            )
            canvas.pack(side='left', expand=True, fill='both')

            scrollbar = Scrollbar(points_label, command=canvas.yview)
            scrollbar.pack(side='right', fill='y')

            canvas.configure(yscrollcommand=scrollbar.set)

            self.frame_point = Frame(
                canvas, width=1800, height=len(self.NAMES_TEAMS) * 26)
            canvas.create_window((0, 0), window=self.frame_point, anchor='nw')

            self.entry_quetion_x_team = [
                [None] + [Entry(self.frame_point, width=6, bd=5,
                                state='readonly', readonlybackground='white')
                          for _ in self._NUMBER_OF_QUESTIONS_RANGE_1]
                for _ in self.NAMES_TEAMS]

            self.stringvar_question_x_team: List[List[IntVar]] = [
                [None] + [IntVar() for _ in self._NUMBER_OF_QUESTIONS_RANGE_1]
                for _ in self.NAMES_TEAMS]

            self.stringvar_question: List[IntVar] = [None] + [IntVar()
                                                              for _ in self._NUMBER_OF_QUESTIONS_RANGE_1]

            self.stringvar_start_row: List[List[StringVar, IntVar]] = [
                [StringVar(), IntVar()] for _ in self.NAMES_TEAMS]

            self.protocol('WM_DELETE_WINDOW',
                          lambda: sys_exit(
                              2 if self._timer_seconds != 0 else 0)
                          if askokcancel("Closing confirm", "All data can be losted.") else None)

    # method about runtime

    def update_main(self):
        """
        Update the values of the timer and questions and record them
        """

        self._timer_seconds -= 1
        self.generate_clock()

        for team in self.NAMES_TEAMS:
            self._recorder.record_total_teams(
                team, self._timer_seconds, self.total_points_team(team))

        for question in self._NUMBER_OF_QUESTIONS_RANGE_1:
            self._recorder.record_values_questions(
                question, self._timer_seconds, self.value_question(question))

    def update_values_questions(self):
        """
        Update the values of questions of 1 if the number of answers is less than the derive
        """
        for question in self._solutions[1:]:
            if question[1] < self._DERIVE:
                question[3] += 1

    # methods about the progress ot time

    def start_competition(self):
        """
        Programming of the scheduler:
            - TOTAL TIME - 30: elimination point's grid
            - TOTAL TIME: elimination of timer label, reconfiguration of main button
            - 1 to TOTAL TIME: update the value of the question
            - 1 to TOTAL TIME - 30: update point's grid
            - Each minute until self._TOTAL_TIME - 1200: update questions' value
            - TOTAL TIME - 30: remove the possibility of giving jolly, assignation jolly at number 1 if possible

        Allow to give answers and jolly
        """

        self.after((self._TOTAL_TIME - self._TIME_FOR_JOLLY)*1000,
                   lambda: [self.submit_jolly(team, 1) for team in self.NAMES_TEAMS])

        self.after((self._TOTAL_TIME - 30)*1000, lambda: [
            widget.grid_forget() for widget in self.frame_point.winfo_children()])

        self.after(self._TOTAL_TIME*10000, lambda: self.main_button.configure(
            state='normal', text="Show ranking", command=self.show_ranking))

        self.after(self._TOTAL_TIME*1000, self.timer_label.destroy)

        for time in range((self._TOTAL_TIME - 30)*1000, self._TOTAL_TIME*1000, 1000):
            self.after(time, self.update_main)

        for time in range(1000, (self._TOTAL_TIME - 30)*1000, 1000):
            self.after(time, self.update_entry)
            self.after(time, self.update_main)

        for time in range(60000, (self._TOTAL_TIME - 1200)*1000, 60000):

            self.after(time, self.update_values_questions)

        self.after((self._TOTAL_TIME - self._TIME_FOR_JOLLY)*1000,
                   lambda: self.arbiterGUI.jolly_button.configure(state='disabled'))

        self.after((self._TOTAL_TIME - self._TIME_FOR_JOLLY)*1000,
                   lambda: [self.submit_jolly(team, 1) for team in self.NAMES_TEAMS])

        self.main_button.configure(state='disabled')
        self.arbiterGUI.jolly_button.configure(state='normal')
        self.arbiterGUI.answer_button.configure(state='normal')

        self.stable_element_builder()

    def show_ranking(self):
        """
        Show the final ranking and configure the main button to save data
        """

        self.main_button.configure(
            text="Save data", command=self._recorder.save)
        self.arbiterGUI.destroy()
        self.stable_element_builder()
        self.update_entry()

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
        Generate labels with the questions' numbers
        Grid all entry whit Stringvar and Intvar
        """

        # Creazione delle etichette per ogni domanda e riga
        for column in self._NUMBER_OF_QUESTIONS_RANGE_1:

            Label(self.frame_point, text=f"{column}", width=6).grid(
                column=column+1, row=0
            )

            Entry(self.frame_point, width=6, bd=5,
                  textvariable=self.stringvar_question[column], state='readonly',
                  readonlybackground='white').grid(column=column+1, row=1)

        for row in range(len(self.NAMES_TEAMS)):

            Label(self.frame_point, anchor='e', textvariable=self.stringvar_start_row[row][0]).grid(
                column=0, row=row+2)

            Entry(self.frame_point, width=6, bd=5,
                  textvariable=self.stringvar_start_row[row][1],
                  state='readonly', readonlybackground='white').grid(column=1, row=row+2)

            for column in self._NUMBER_OF_QUESTIONS_RANGE_1:

                self.entry_quetion_x_team[row][column].configure(
                    textvariable=self.stringvar_question_x_team[row][column])
                self.entry_quetion_x_team[row][column].grid(
                    column=column+1, row=row+2)

    def update_entry(self):
        """
        Update values in points
        """

        # Create value labels for each question
        for question in self._NUMBER_OF_QUESTIONS_RANGE_1:

            self.stringvar_question[question].set(
                self.value_question(question))

        # Populate team points and color-code entries
        for row, team in enumerate(sorted(self.NAMES_TEAMS,
                                          key=self.total_points_team,
                                          reverse=True)):

            self.stringvar_start_row[row][0].set(team)

            self.stringvar_start_row[row][1].set(self.total_points_team(team))

            for question in self._NUMBER_OF_QUESTIONS_RANGE_1:

                points = self.value_question_x_squad(team, question)

                self.stringvar_question_x_team[row][question].set(
                    self.value_question_x_squad(team, question))

                self.entry_quetion_x_team[row][question].config(
                    readonlybackground='red' if points < 0 else 'green' if points > 0 else 'white',
                    fg='blue' if self._list_point[team][question][2] == 2 else 'black')

    # methods to submit answer or jolly

    def submit_answer(self, selected_team: str, entered_question: int, entered_answer: int):
        """
        The mehtod to submit answers
        """

        if not 0 < entered_question <= self._NUMBER_OF_QUESTIONS or selected_team not in self.NAMES_TEAMS:
            return

        data_point_team = self._list_point[selected_team][entered_question]
        data_question = self._solutions[entered_question]

        # if is unanswered
        if data_point_team[1] == 0:

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
                data_question[2] += (1 if data_point_team[0]
                                     == 1 else 0)

        self._recorder.record_answer(
            selected_team, entered_question, entered_answer)

    def submit_jolly(self, selected_team: str, entered_question: int):
        """
        The method to submit jolly

        """

        self._list_point[selected_team][1][2] = 1
        # check timer staus and if other jolly are already been given

        if 0 < entered_question <= self._NUMBER_OF_QUESTIONS and selected_team in self.NAMES_TEAMS and sum(question[2]
                                                                                                           for question in self._list_point[selected_team][1:]
                                                                                                           ) == self._NUMBER_OF_QUESTIONS:

            # adding jolly
            self._list_point[selected_team][entered_question][2] = 2
            self._recorder.record_jolly(selected_team, entered_question)

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
        ) * list_point_team[2]

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
        set_icon(self)

        Label(self, text="Team:").pack()
        self.team_var = StringVar()
        Combobox(
            self,
            textvariable=self.team_var,
            values=main.NAMES_TEAMS,
            state='readonly'
        ).pack()

        Label(self, text="Question number:").pack()
        self.question_var = IntVar()
        Entry(self, textvariable=self.question_var).pack()

        Label(self, text="Answer:").pack()
        self.answer_var = IntVar()
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
