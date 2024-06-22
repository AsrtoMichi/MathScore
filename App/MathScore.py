#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GUI
import configparser
from typing import Union, Literal
from tkinter import Tk, Toplevel, Canvas, StringVar, Entry, Label
from tkinter.ttk import Frame, Button, Scrollbar, Combobox

# os
from threading import Thread

# .ini reading
from configparser import ConfigParser
from ast import literal_eval
from os.path import join, dirname
import sys


# Gestion of errors:
#   Sonfigration errors 10-19:
#       10 Unable to load data
#       11 Error reading the configuration file
#   Saving data errors 20-29:
#       20 Unable to save data
# 30 Conclusion during the competions

class Recorder:

    def __init__(self, names_teams: list, number_question: int, total_time: int, base_points: int):

        self._jolly = {name: 0 for name in names_teams}
        self._answer = {name: [(total_time, base_points)]
                        for name in names_teams}
        self._values_questions = {
            question: [(total_time, base_points)]
            for question in range(1, number_question+1)
        }
        self._total_teams = {name: []
                             for name in names_teams}

    def record_jolly(self, name_team: str, question: int):
        self._jolly[name_team] = question

    def record_ansewer(self, name_team: str, time: int, answer: int):
        self._answer[name_team].append((time, answer))

    def record_values_questions(self, question: int, time: int, value: int):
        if self._values_questions[question][-1][1] != value:
            self._values_questions[question].append((time, value))

    def record_total_teams(self, name_team: str, time: int, value: int):
        self._total_teams[name_team].append((time, value))

    def __str__(self):
        return str((self._jolly, self._answer, self._values_questions, self._total_teams))


class Main(Tk):

    """
    That class is the main window: here are showed poits
    """

    def __init__(self):

        try:
            config = ConfigParser()
            config.read(join(dirname(__file__), 'config.ini')
                        if len(sys.argv) == 1 else sys.argv[1])

        except Exception:

            from tkinter.messagebox import showerror
            showerror(
                "Error", f"Unable to find the config.ini file")
            exit(11)

        try:

            # teams' names
            self.NAMES_TEAMS = tuple(config.get('Teams', 'teams').split(', '))

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

            # creation solutions dict
            self._solutions = {
                i + 1: {'xm': solution, 'correct': 0, 'incorrect': 0, 'value':  config.getint('Points', 'vantage')}
                for i, solution in enumerate(literal_eval(config.get('Solutions', 'solutions')))
            }
            self._NUMBER_OF_QUESTIONS = len(self._solutions)

            # list point, bonus, n_fulled
            self._list_point = {name: [self._NUMBER_OF_QUESTIONS * 10] + [{'errors': 0, 'status': 0, 'jolly': 1, 'bonus': 0}
                                                                          for _ in range(self._NUMBER_OF_QUESTIONS)] for name in self.NAMES_TEAMS}
            self._fulled = 0

            # data recording
            self._NAME_FILE = config.get('Recording', 'name_file'),
            self._DIRECTORY_RECORDING = config.get(
                'Recording', 'directory_recording')
            self._data_saving_success = False

            self._recorder = Recorder(
                self.NAMES_TEAMS, self._NUMBER_OF_QUESTIONS, self._TOTAL_TIME, self._NUMBER_OF_QUESTIONS * 10)

        except configparser.NoSectionError:

            from tkinter.messagebox import showerror
            showerror(
                "Error", f"An error orccured reading the config.ini file")
            exit(11)

        else:

            # creation Main window and castomization
            super().__init__()
            self.title("Competitors")
            self.geometry("1850x630")
            self.resizable(True, False)
            self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

            # widget costruction
            self.timer_label = Label(self, font=('Helvetica', 18, 'bold'))
            self.timer_label.pack()
            self.start_button = Button(
                self, text="Start", command=self.start_competition)
            self.start_button.pack()
            self.generate_clock()

            self.protocol("WM_DELETE_WINDOW", lambda: exit(3 if self._timer_seconds !=
                                                           0 else 2 if self._data_saving_success else 0))

    # methods about the progress ot time

    def start_competition(self):
        """
        Initialise the timer and block start buttom
        """
        self.arbiter_GUI = Arbiter_GUI(self)
        self.jolly_GUI = Jolly_GUI(self)

        self.start_button.config(state='disabled')

        self.point_label_costructor()
        self.update_timer()

    def show_ranking(self):
        self.arbiter_GUI.destroy()
        self.point_label_costructor()
        self.ranking_button.configure(state='disabled')

    def update_timer(self):
        """
        Update timer and launch bot
        Is the most impotant metod for the 
        """

        # if time is finished
        if self._timer_seconds == 0:

            try:

                open(join(self._DIRECTORY_RECORDING,
                          f"{self._NAME_FILE}.txt"), 'w').write(str(self._recorder))
                self._data_saving_success = True

            except Exception:

                from tkinter.messagebox import showerror
                showerror(
                    "Error",
                    f"An error occurred saving data, data will be printed in the terminal.",
                )
                print(str(self._recorder))

            finally:

                self.start_button.destroy()
                self.timer_label.destroy()
                self.ranking_button = Button(self, text="Show ranking",
                                             command=self.show_ranking, width=30)
                self.ranking_button.pack()

        else:

            self._timer_seconds -= 1
            self.generate_clock()

            # update points each minut
            if self._timer_seconds % 60 == 0:
                Thread(target=self.bot()).start

            if self._timer_seconds == (self._TOTAL_TIME - self._TIME_FOR_JOLLY):
                self.jolly_GUI.destroy()

            # remove point label befor the end
            if self._timer_seconds == 30:
                self.points_label.destroy()

            self.after(50, self.update_timer)

    def bot(self):
        """
        Increase poits amutomaticaly
        """
        for question in self._solutions.keys():
            if (
                self._solutions[question]['correct'] < self._DERIVE
                and self._timer_seconds >= 1200
            ):
                self._solutions[question]['value'] += 1

        if self._timer_seconds >= 30:
            self.update_entry()

        for team in self.NAMES_TEAMS:
            self._recorder.record_total_teams(
                team, self._timer_seconds, self.total_squad_point(team))

        for question in range(1, self._NUMBER_OF_QUESTIONS+1):
            self._recorder.record_values_questions(
                question, self._timer_seconds, self.point_answer(question))

    # metods about wiget

    def generate_clock(self):
        """
        Generate the clock label
        """
        self.timer_label.config(
            text=f"Time left: {self._timer_seconds // 3600: 02}: {(self._timer_seconds % 3600) // 60: 02}: {self._timer_seconds % 60: 02}"
        )

    def point_label_costructor(self):
        """
        Generate canvas whit scrollbar for ranking
        """

        self.points_label = Frame(self, width=1800, height=600)
        self.points_label.pack(pady=20)

        # Creazione del canvas all'interno dell'etichetta dei punti
        canvas = Canvas(
            self.points_label,
            width=1800,
            height=600,
            scrollregion=(0, 0, 1800, len(self.NAMES_TEAMS) * 26),
        )
        canvas.pack(side='left', expand=True, fill='both')

        # Aggiunta di una barra di scorrimento verticale
        scrollbar = Scrollbar(self.points_label, command=canvas.yview)
        scrollbar.pack(side='right', fill='y')

        canvas.config(yscrollcommand=scrollbar.set)

        self.frame_point = Frame(
            canvas, width=1800, height=len(self.NAMES_TEAMS) * 26)
        canvas.create_window((0, 0), window=self.frame_point, anchor='nw')

        # Creazione delle etichette per ogni domanda e riga
        for question in range(2, self._NUMBER_OF_QUESTIONS + 2):
            Label(self.frame_point, text=f"{question+1}", width=6).grid(
                column=question, row=0
            )

        self.update_entry()

    def update_entry(self):
        """
        Update ranking
        """

        # Clear all widgets in the frame except protected columns
        for widget in self.frame_point.winfo_children():
            if widget.grid_info()['row'] != 0:
                widget.destroy()

        # Create value labels for each question
        for question in range(self._NUMBER_OF_QUESTIONS):
            value_label = Entry(self.frame_point, width=6, bd=5)
            value_label.insert(0, str(self.point_answer(question+1)))
            value_label.grid(column=question + 2, row=1)

        # Populate team points and color-code entries
        for row, frame in enumerate(
            sorted(
                [(self.total_squad_point(team), team)
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
            total_num.insert(0, str(self.total_squad_point(team)))
            total_num.grid(column=1, row=row)

            for column in range(1, self._NUMBER_OF_QUESTIONS + 1):

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
        if self._list_point[selected_team][entered_question]['status'] == 0:

            # if correct
            if entered_answer == self._solutions[entered_question]['xm']:

                self._list_point[selected_team][entered_question]['status'] = 1
                self._list_point[selected_team][entered_question]['bonus'] = self._BONUS_ANSWER[min(
                    self._solutions[entered_question]['correct'], self._N_BONUS_ANSWER)]
                self._solutions[entered_question]['correct'] += 1

                # give bonus
                if (
                    sum(
                        [
                            team['status']
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
                self._list_point[selected_team][entered_question]['errors'] += 1
                self._solutions[entered_question]['incorrect'] += (
                    1
                    if self._list_point[selected_team][entered_question]['errors']
                    == 1
                    else 0
                )

        self._recorder.record_ansewer(
            selected_team, entered_question, entered_answer)

        self.update_entry()

    def submit_jolly(self, selected_team: str, entered_question: int):
        """
        the metod to submit a jolly
        """
        # check timer staus and if other jolly are already been given
        if self._timer_seconds > (self._TOTAL_TIME - 600) and (
            sum(
                [
                    question['jolly']
                    for question in self._list_point[selected_team][1:]
                ]
            )
            == self._NUMBER_OF_QUESTIONS
        ):
            # adding jolly
            self._list_point[selected_team][entered_question]['jolly'] = 2
            self._recorder.record_jolly(selected_team, entered_question)
            self.update_entry()

    # methods to calculate points
    def point_answer(self, question: int) -> int:
        """
        Return the value of answer
        """
        try:
            answer_data = self._solutions[question]
            return int(answer_data['value'] + answer_data['incorrect'] * 2)
        except IndexError:
            return 0

    def point_answer_x_squad(
        self, team: str, question: Union[Literal['base'], int], jolly_simbol: bool = False
    ) -> Union[int, str]:
        """
        Return the points made a team in a question
        """
        answer_point = self._list_point[team][question]

        # Calculate the output points
        result = (
            answer_point['status'] * self.point_answer(question)
            - answer_point['errors'] * 10
            + answer_point['bonus']
        ) * answer_point['jolly']

        return (
            f"{result} J"
            if answer_point['jolly'] == 2 and jolly_simbol
            else result
        )

    def total_squad_point(self, team: str) -> int:
        """
        Return the point of a team
        """
        return sum(self.point_answer_x_squad(team, question)
                   for question in range(1, self._NUMBER_OF_QUESTIONS+1)
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
