#!/usr/bin/env pypy3
# -*- coding: utf-8 -*-

# GUI
from tkinter import Tk, Toplevel, Canvas, StringVar, Entry, Label
from tkinter.ttk import Frame, Button, Scrollbar, Combobox

# os
from threading import Thread

# class File
from configparser import ConfigParser
from ast import literal_eval
from os.path import join, dirname
from typing import Union, Literal, Tuple


class File:
    """
    Class that is method collector regarding files
    """

    @staticmethod
    def get_config() -> tuple:
        """
        A metod to get configurtios from config.ini
        """
        try:

            config = ConfigParser()
            config.read(join(dirname(__file__), "config.ini"))

            return (
                tuple(config.get("Teams", "teams").split(", ")),
                config.getint("Competition", "time"),
                config.getint("Competition", "vantage"),
                config.getint("Competition", "DERIVE"),
                literal_eval(config.get("Solutions", "solutions")),
                config.get("Recording", "name_file"),
                config.get("Recording", "directory_recording"),
            )
        except Exception as e:
            from tkinter.messagebox import showerror
            showerror(
                "Error", f"Unable to complete configuration.  Details: {str(e)}")
            from sys import exit
            exit()

    @staticmethod
    def save_data(directory: str, name: str, data: Tuple[dict, list]):
        """
        A metod to save data in a .txt file
        """
        try:

            open(join(directory, f"{name}.txt"), 'w').write(str(data))

        except Exception as e:

            from tkinter.messagebox import showerror
            showerror(
                "Error",
                f"An error occurred, data will be printed in the terminal.  Details: {str(e)}",
            )
            print(data)


class Main(Tk):

    """
    That class is the main window: here are showed poits
    """

    # methods about wiget
    def __init__(self):

        # cration Main window and castomization
        super().__init__()
        self.title("Competitors")
        self.geometry(f"1850x630")
        self.resizable(True, False)
        self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

        # collecting data
        data = File.get_config()

        # teams' names
        self.NAMES_TEAMS = data[0]

        # genaration timer
        self.total_time = self.timer_seconds = data[1]
        self.timer_status = 0
        self.timer_label = Label(self, font=('Helvetica', 18, 'bold'))

        # widget costruction
        self.timer_label.pack()
        self.start_button = Button(
            self, text="Start", command=self.start_clock)
        self.start_button.pack()
        self.generate_clock()

        # setting DERIVE and creation solutions dict
        self.DERIVE = data[3]
        self.solutions = {
            i + 1: {'xm': solution, 'correct': 0, 'incorrect': 0, 'value': data[2]}
            for i, solution in enumerate(data[4])
        }
        self.NUMBER_OF_QUESTIONS = len(self.solutions)

        # list point, bonus, n_fulled
        base_points = self.NUMBER_OF_QUESTIONS * 10
        self.list_point = {name: {'base': base_points, **{question+1: {'errors': 0, 'status': 0, 'jolly': 1,
                                                                       'bonus': 0} for question in range(self.NUMBER_OF_QUESTIONS)}} for name in self.NAMES_TEAMS}

        self.fulled = 0

        # data recording
        self.recording_teams, self.recording_question, self.name_file, self.directory_recording = (
            {name: [(0, 220)] for name in self.NAMES_TEAMS},
            [(0, (0 for _ in range(self.NUMBER_OF_QUESTIONS)))],
            data[5],
            data[6],
        )

    def update_entry(self):
        """
        Update Labels
        """

        # Clear all widgets in the frame except protected columns
        for widget in self.frame_point.winfo_children():
            if widget.grid_info()['row'] != 0:
                widget.destroy()

        # Create value labels for each question
        for question in range(self.NUMBER_OF_QUESTIONS):
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

            for column in range(1, self.NUMBER_OF_QUESTIONS + 1):

                points = self.point_answer_x_squad(team, column)

                total_num = Entry(self.frame_point, width=6, bd=5,
                                  bg='red' if points < 0 else 'green' if points > 0 else 'white')
                total_num.insert(
                    0, self.point_answer_x_squad(team, column, True))
                total_num.grid(column=column + 1, row=row)

        Thread(target=self.collect_values_question()).start()

    # methods about time and timer label

    def start_clock(self):
        """
        Initaialise the timer and block start buttom
        """
        Arbiter_GUI(self)
        Jolly_GUI(self)

        self.start_button.config(state='disabled')
        self.timer_status = 1

        points_label = Frame(self, width=1800, height=600)
        points_label.pack(pady=20)

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

        canvas.config(yscrollcommand=scrollbar.set)

        self.frame_point = Frame(
            canvas, width=1800, height=len(self.NAMES_TEAMS) * 26)
        canvas.create_window((0, 0), window=self.frame_point, anchor='nw')

        # Creazione delle etichette per ogni domanda e riga
        for question in range(2, self.NUMBER_OF_QUESTIONS + 2):
            Label(self.frame_point, text=f"{question+1}", width=6).grid(
                column=question, row=0
            )

        self.update_timer()
        self.update_entry()

    def generate_clock(self):
        """
        Generate the clock label
        """
        self.timer_label.config(
            text=f"Time left: {self.timer_seconds // 3600:02}:{(self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}"
        )

    def update_timer(self):
        """
        Update timer and launch bot
        """

        if self.timer_status == 1:

            if self.timer_seconds > 0:

                self.timer_seconds -= 1
                self.generate_clock()

                if self.timer_seconds % 60 == 0:
                    Thread(target=self.bot()).start

                self.after(1000, self.update_timer)

            elif self.timer_seconds == 0:
                self.timer_status = 2
                File.save_data(self.directory_recording,
                               self.name_file, self.recording_teams)
                self.winfo_children()[3].destroy()
                self.winfo_children()[2].destroy()

    def bot(self):
        """
        Increase poits amutomaticaly
        """
        for question in self.solutions.keys():
            if (
                self.solutions[question]['correct'] < self.DERIVE
                and self.timer_seconds >= 1200
            ):
                self.solutions[question]['value'] += 1

        self.update_entry()

    def collect_values_question(self):
        self.recording_question.append((self.timer_seconds, (self.point_answer(
            question+1) for question in range(self.NUMBER_OF_QUESTIONS))))

    # methods to submit answer

    def submit_answer(
        self, selected_team: str, entered_question: int, entered_answer: int
    ):
        """
        the metod to submit an answer
        """

        # if is unanswered
        if self.list_point[selected_team][entered_question]['status'] == 0:

            # if correct
            if entered_answer == self.solutions[entered_question]['xm']:
                self.solutions[entered_question]['correct'] += 1
                self.list_point[selected_team][entered_question]['status'] = 1
                self.list_point[selected_team][entered_question]['bonus'] = (
                    20,
                    15,
                    10,
                    5,
                    3,
                    0,
                )[min(self.solutions[entered_question]['correct'], 6) - 1]

                if (
                    sum(
                        [
                            team['status']
                            for team in self.list_point[selected_team].values()
                            if type(team) is dict
                        ]
                    )
                    == self.NUMBER_OF_QUESTIONS
                ):
                    self.fulled += 1
                    self.list_point[selected_team]['base'] += (
                        50,
                        30,
                        20,
                        15,
                        10,
                        0,
                    )[min(self.fulled, 6) - 1]

            # if wrong
            else:
                self.list_point[selected_team][entered_question]['errors'] += 1
                self.solutions[entered_question]['incorrect'] += (
                    1
                    if self.list_point[selected_team][entered_question]['errors']
                    == 1
                    else 0
                )

        self.update_entry()

        self.recording_teams[selected_team].append(
            (
                self.total_time - self.timer_seconds,
                self.total_squad_point(selected_team),
            )
        )

    def submit_jolly(self, selected_team: str, entered_question: int):
        """
        the metod to submit a jolly
        """
        # check timer staus
        if self.timer_seconds > (self.total_time - 600):
            # check if other jolly are been given
            if (
                sum(
                    [
                        question['jolly']
                        for question in self.list_point[selected_team].values()
                        if type(question) is dict
                    ]
                )
                == self.NUMBER_OF_QUESTIONS
            ):
                # adding jolly
                self.list_point[selected_team][entered_question]['jolly'] = 2
                self.update_entry()

    # methods to calculate points
    def point_answer(self, question: int) -> int:
        """
        Return the value of answer
        """
        if question <= self.NUMBER_OF_QUESTIONS:
            answer_data = self.solutions[question]
            return int(answer_data['value'] + answer_data['incorrect'] * 2)

    def point_answer_x_squad(
        self, team: str, question: Union[Literal['base'], int], jolly_simbol: bool = False
    ) -> Union[int, str]:
        """
        Return the points made a team in a question
        """
        # Check if the team is in the list of teams
        if team in self.NAMES_TEAMS:

            # If the question is "base", return the sum of base points
            if question == 'base':
                return self.list_point[team]['base']

            # If the question number is within the total number of questions
            elif question <= self.NUMBER_OF_QUESTIONS:
                # Get the points for the specific question
                answer_point = self.list_point[team][question]

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
        if team in self.NAMES_TEAMS:
            return sum(
                self.point_answer_x_squad(team, question)
                for question in self.list_point[team].keys()
            )


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

    def submit_answer(self):
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

        except:
            pass

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

    def submit_jolly(self):
        """
        The method associated to the button
        """
        try:
            Thread(
                target=self.self.submit_jolly_main(
                    self.selected_team_jolly.get(), int(self.question_entry_jolly.get())
                )
            ).start

        except:
            pass
        self.selected_team_jolly.set("")
        self.question_entry_jolly.delete(0, "end")


if __name__ == "__main__":

    #from cProfile import run
    #run('Main()')
    Main().mainloop()
