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
from tkinter.ttk import Button, Scrollbar, Combobox
from tkinter.filedialog import askopenfilename, asksaveasfile
from tkinter.messagebox import askokcancel, showerror, showwarning
from _tkinter import TclError

# OS
from sys import exit as sys_exit
# sys_exit is used to prevent problem exe version

# .ini reading
from configparser import ConfigParser, ParsingError
from ast import literal_eval
from os.path import join, dirname, abspath
from os import access, stat


class Recorder:

    """
    This class is used for save:
    - answer given by a team
    - jolly chosen for a team
    """

    def __init__(self, names):

        self._jolly = {name: None for name in names}
        self._answer = {name: [] for name in names}

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


class StringVar(Variable):
    """Value holder for strings variables."""
    _default = ""

    def __init__(self, master=None, value=None):
        """Construct a string variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to "")
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        Variable.__init__(self, master, value)

    def set(self, value=""):
        """Set the variable to VALUE."""
        self._tk.globalsetvar(self._name, value)


class IntVar(StringVar):
    """Value holder for integer variables."""

    def __init__(self, master=None, value=None):
        """Construct an integer variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to 0)
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        StringVar.__init__(self, master, value)

    def get(self) -> int:
        """Return the value of the variable as an integer."""
        value = self._tk.globalgetvar(self._name)
        try:
            return int(value)
        except ValueError:
            return 0


class Main(Tk, Recorder):

    """
    Is the main window: here are showed poits
    """

    def __init__(self):
        """
        Step of init method:

        0. Creation of the main Window:
            modification of WM_DELETE_WINDOW to prevent accidental closures:
                Error code 3 if the windows are closed during the competition

        1. Individuate the .ini file:
            1. in the same directory
            2. ask to the user
                Error exit code: 20 "No .ini file has been give."
            3.check if the config.ini exists/possibly open it:
                Error exit code: 21 "Impossible to read the config.ini file."

        2. reading of file using ConfigParser:
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

            Error exit code: KeyError, ValueError, ParsingError ValueError 22
                "An error occurred reading the config.ini file"


        3. - creation of ArbiterGUI
           - the creation of a timer label
           - the creation of the main button
           - the creation of a scrollable area for the point's grid
           - creation of the list of IntVar e StringVar ad Entry to show points
           - connctio var to entry
           - griding entry
        """

        # ---------------- 0. Main general config ---------------- #

        Tk.__init__(self)
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', lambda: self.exit_confirm(3))

        try:
            self.iconbitmap(default=abspath(
                join(dirname(__file__), 'MathScore.ico')))
        except TclError:
            pass

        Label(self, text='Copyright(C) 2024 AstroMichi').pack(
            side='bottom', anchor="e", padx=8, pady=8)

        ini_file_path = abspath(join(dirname(__file__), 'Config.ini'))
        # serch the ini file in the same directory

        # ---------------- 1. Individation config.ini ---------------- #

        try:
            stat(ini_file_path)

        except OSError:

            # if ther isn't the ini file in the same path ask to the user to select the file
            ini_file_path = askopenfilename(
                parent=self,
                title='Select the .ini file',
                filetypes=[('Initiation File Format', '*.ini')])

            if not ini_file_path:

                self.exit_error('No .ini file has been gived.', 20)
        else:

            if not access(ini_file_path, 4):
                self.exit_error(
                    'Impossible to read the config.ini file.', 21,
                    PermissionError(13, 'Not enough permissions.', ini_file_path, None))

        # ------------------- 2. Parsing config.ini ------------------- #
        try:
            config = ConfigParser()
            config.read(ini_file_path)

            self.NAMES_TEAMS = tuple(config['Generic']['teams'].split(', '))

            self._timer_seconds = int(
                config['Timer']['time'])*60

            self._TIME_FOR_JOLLY = int(config['Timer']['time_for_jolly'])*60

            # DERIVE is the minum number of question to block the grow of the value of a question
            self._DERIVE = int(config['Points']['derive'])

            self._BONUS_ANSWER = literal_eval(
                config['Points']['bonus_answer'])
            self._N_BONUS_ANSWER = len(self._BONUS_ANSWER) - 1

            for bonus in self._BONUS_ANSWER:
                if not isinstance(bonus, int):
                    raise ValueError

            self._BONUS_FULLED = literal_eval(
                config['Points']['bonus_fulled'])
            self._N_BONUS_FULLED = len(self._BONUS_FULLED) - 1

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

            self._solutions = [0] + [
                [solution,  0,  0, value]
                for solution in solutions
            ]

            self._NUMBER_OF_QUESTIONS = len(solutions)

            self._NUMBER_OF_QUESTIONS_RANGE_1 = range(
                1, self._NUMBER_OF_QUESTIONS + 1)

            # 0: errors
            # 1: status
            # 2: jolly
            # 3: bonus

            self._list_point = {
                name: [self._NUMBER_OF_QUESTIONS * 10] + [[0]*4
                                                          for _ in self._NUMBER_OF_QUESTIONS_RANGE_1
                                                          ]for name in self.NAMES_TEAMS}

            Recorder.__init__(self, self.NAMES_TEAMS)

        except (KeyError, ValueError, ParsingError, TypeError) as e:
            self.exit_error(
                'An error occurred parsing the config.ini file', 22, e)

        # ---------------------- 3. Buliding Main ---------------------- #
        else:

            self.title(config['Generic']['name_competion'])

            self.arbiterGUI = ArbiterGUI(self)

            # ------------------- Timer Label ------------------- #
            self.timer_label = Label(self, font=('Helvetica', 18, 'bold'),
                                     text=f'Time left: {self._timer_seconds // 3600:02d}:{(self._timer_seconds % 3600) // 60:02d}:00')
            self.timer_label.pack()

            # ------------------- Main Button ------------------- #

            self.main_button = Button(
                self, text="Start", command=self.start_competition)
            self.main_button.pack()

            # ----------------- Scrollable Area ----------------- #

            self.canvas = Canvas(self)
            self.scrollbar = Scrollbar(
                self, orient='vertical', command=self.canvas.yview)
            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            colum_range = range(2, self._NUMBER_OF_QUESTIONS+2)
            # ----------------- Head columns ----------------- #

            self.var_question = [None]

            for col in colum_range:

                Label(self.canvas, width=6, text=col).grid(row=0, column=col)

                question_var = IntVar(self)

                Entry(self.canvas, width=6, bd=5,
                      state='readonly', readonlybackground='white',
                      textvariable=question_var
                      ).grid(row=1, column=col)

                self.var_question.append(question_var)

            # ---------------------- Rows ---------------------- #

            self.var_start_row = []
            self.var_question_x_team = []
            self.entry_question_x_team = []

            for row in range(2, len(self.NAMES_TEAMS)+2):

                team_var, total_points_team_var = StringVar(self), IntVar(self)

                Label(self.canvas, anchor='e',
                      textvariable=team_var
                      ).grid(row=row, column=0)

                Entry(self.canvas, width=6, bd=5,
                      state='readonly', readonlybackground='white',
                      textvariable=total_points_team_var
                      ).grid(row=row, column=1)

                self.var_start_row.append((team_var, total_points_team_var))

                var_list = [None]
                entry_list = [None]

                for col in colum_range:

                    points_team_x_question = IntVar(self)

                    entry = Entry(self.canvas, width=6, bd=5,
                                  state='readonly', readonlybackground='white',
                                  textvariable=points_team_x_question
                                  )

                    entry.grid(row=row, column=col)

                    var_list.append(points_team_x_question)
                    entry_list.append(entry)

                self.var_question_x_team.append(var_list)
                self.entry_question_x_team.append(entry_list)

            self.update_entry()

    # -------------------- Runtime's -------------------- #

    def start_competition(self):
        """
        Programming of the scheduler:
            - TOTAL TIME - 30: elimination point's grid
            - TOTAL TIME: elimination of timer label, reconfiguration of main button
            - 1 to TOTAL TIME: update the value of the question
            - 1 to TOTAL TIME - 30: update point's grid
            - Each minute until self._TOTAL_TIME - 1200: update questions' value
            - TOTAL TIME - 30: remove the possibility of giving jolly,
              assignation jolly at number 1 if possible

        Allow to give answers and jolly
        """

        TOTAL_TIME = self._timer_seconds

        # -------------------- Start -------------------- #

        self.canvas_scrollbar_pack()

        self.main_button.configure(state='disabled')
        self.arbiterGUI.jolly_button.configure(state='normal')
        self.arbiterGUI.answer_button.configure(state='normal')
        self.bind('< Return >', lambda key: self.arbiterGUI.submit_answer)

        # -------------- Repetitive functions -------------- #

        for time in range(1000, (TOTAL_TIME*1000)+1, 1000):
            self.after(time, self.update_timer)

        for time in range(60000, ((TOTAL_TIME - 1200)*1000)+1, 60000):
            self.after(time, self.update_values_questions)

        # ------------------- Stop jolly ------------------- #

        self.after(self._TIME_FOR_JOLLY*1000,
                   self.arbiterGUI.jolly_button.configure, {'state': 'disabled'})

        self.after(self._TIME_FOR_JOLLY*1000,
                   lambda: [self.submit_jolly(team, 1) for team in self.NAMES_TEAMS])

        # ----------------- Hinding points ----------------- #

        self.after((TOTAL_TIME - 30)*1000, self.canvas_scrollbar_pack_forget)

        # ------------------- Conclusion ------------------- #

        self.after(TOTAL_TIME*1000, self.main_button.configure,
                   {'state': 'normal', 'text': 'Show ranking', 'command': self.show_ranking})

        self.after(TOTAL_TIME*1000, self.timer_label.destroy)

    def show_ranking(self):
        """
        Show the final ranking and configure the main button to save data
        """

        self.main_button.configure(
            text='Save data', command=self.save_data)
        self.arbiterGUI.destroy()
        self.canvas_scrollbar_pack()

    def save_data(self):
        """
        Try to save data if is not possible copy them in clipboard
        """

        data = str(self._jolly, self._answer)

        try:
            asksaveasfile().write(data)
        except SyntaxError:
            pass
        except OSError as e:
            self.clipboard_append(data)
            showwarning('Saving failled',
                        'Data copied in to the clipboard',
                        deatil=e, parent=self)

    # --------------------- Grafic's --------------------- #

    def canvas_scrollbar_pack(self):
        """
        Pack canvas for entryes and scrollbarr
        """

        self.tk.call('pack', 'configure', '.!scrollbar', '.!canvas',
                     '-expand', 'yes',
                     '-fill', 'both',
                     '-side', 'right')

    def canvas_scrollbar_pack_forget(self):
        """
        Pack forget canvas for entryes and scrollbarr
        """
        self.tk.call('pack', 'forget', '.!scrollbar', '.!canvas')

    # --------------.------ Upadte's --------------------- #

    def update_timer(self):
        """
        Update the clock label
        """

        self._timer_seconds -= 1
        self.timer_label.configure(
            text=f"Time left: {self._timer_seconds // 3600:02d}: {(self._timer_seconds % 3600) // 60:02d}: {self._timer_seconds % 60:02d}"
        )

    def update_values_questions(self):
        """
        Update the values of questions of 1 if the number of answers is less than the derive
        """
        for question in self._solutions[1:]:
            if question[1] < self._DERIVE:
                question[3] += 1

    def update_entry(self):
        """
        Update values in points
        """

        # Create value labels for each question
        for question in self._NUMBER_OF_QUESTIONS_RANGE_1:

            self.var_question[question].set(
                self.value_question(question))

        # Populate team points and color-code entries
        for row, team in enumerate(sorted(self.NAMES_TEAMS,
                                          key=self.total_points_team,
                                          reverse=True)):

            self.var_start_row[row][0].set(team)

            self.var_start_row[row][1].set(self.total_points_team(team))

            for question in self._NUMBER_OF_QUESTIONS_RANGE_1:

                points = self.value_question_x_squad(team, question)

                self.var_question_x_team[row][question].set(points)

                self.entry_question_x_team[row][question].config(
                    readonlybackground='red' if points < 0 else 'green' if points > 0 else 'white',
                    fg='blue' if self._list_point[team][question][2] else 'black',
                    font=f"Helvetica 9 {'bold' if self._list_point[team][question][2] else 'normal'}")

    # --------------------- Dialog's --------------------- #

    def exit_error(self, message: str, error_code: int, details: Exception = None):
        """
        Give advice about fatal error
        """

        showerror(
            'Error', message,
            parent=self,
            detail=f'Exit code {error_code}\n{details}')
        sys_exit(error_code)

    def exit_confirm(self, exit_code: int = 0):
        """
        Ask confirm before closing the program
        """

        if askokcancel('Confirm exit', 'Data can be losted.',
                       detail=f'Exit code {exit_code}', parent=self):
            sys_exit(exit_code)

    # --------------------- Submit's --------------------- #

    def submit_answer(self, team: str, question: int, answer: int):
        """
        The mehtod to submit answers
        """

        if question in self._NUMBER_OF_QUESTIONS_RANGE_1:

            data_point_team = self._list_point[team][question]
            data_question = self._solutions[question]

            # if is unanswered
            if not data_point_team[1]:

                # if correct
                if answer == data_question[0]:

                    data_point_team[1] = 1

                    data_point_team[3] = self._BONUS_ANSWER[min(
                        data_question[1], self._N_BONUS_ANSWER)]

                    data_question[1] += 1

                    # give bonus
                    if sum(question[1]
                            for question in self._list_point[team][1:]
                           ) == self._NUMBER_OF_QUESTIONS:

                        self._list_point[team][0] += self._BONUS_FULLED[min(
                            self._solutions[0], self._N_BONUS_FULLED)]
                        self._solutions[0] += 1

                # if wrong
                else:
                    data_point_team[0] += 1
                    data_question[2] += 1 if data_point_team[0] else 0

        self.update_entry()

        self.record_answer(
            team, self._timer_seconds, question, answer)

    def submit_jolly(self, team: str, question: int):
        """
        The method to submit jolly
        """

        # check if other jolly are already been given
        if question in self._NUMBER_OF_QUESTIONS_RANGE_1 and not sum(question[2]
                                                                     for question in self._list_point[team][1:]
                                                                     ):

            # adding jolly
            self._list_point[team][question][2] = 1
            self.record_jolly(team, self._timer_seconds, question)

            self.update_entry()

    # ---------------- Point's calculation ---------------- #

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

        self.title('Reciver')
        self.geometry('250x290')
        self.resizable(False, False)

        Label(self, text="Team:").pack()
        self.team_var = StringVar()
        Combobox(
            self,
            textvariable=self.team_var,
            values=main.NAMES_TEAMS,
            state='readonly'
        ).pack()

        Label(self, text="Question number:").pack()
        self.question_var = IntVar(self)
        Entry(self, textvariable=self.question_var,
              validate='key', vcmd=(self.register(lambda text: 1 if text.isdigit() and 0 < int(text) < 24 else not text), '%P')).pack()

        Label(self, text="Answer:").pack()
        self.answer_var = IntVar(self)
        Entry(self, textvariable=self.answer_var,
              validate='key', vcmd=(self.register(lambda text: 1 if text.isdigit() and len(text) <= 4 else not text), '%P')).pack()

        self.jolly_button = Button(
            self, text="Submit Jolly", command=self.submit_jolly, state='disabled')
        self.jolly_button.pack(pady=15)

        self.answer_button = Button(
            self, text="Submit Answer", command=self.submit_answer, state='disabled')
        self.answer_button.pack()

        Label(self, text='Copyright (C) 2024 AstroMichi').pack(
            side='bottom', anchor="e", padx=8, pady=8)

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

    Main().mainloop()
