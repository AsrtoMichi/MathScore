#!/usr/bin/env pypy3
# -*- coding: utf-8 -*-

# GUI
from tkinter import Tk, Toplevel, Canvas, StringVar, Entry, Label
from tkinter.ttk import Frame, Button, Scrollbar, Combobox
from tkinter.messagebox import showerror

# os
from sys import exit
from threading import Thread

# class File
from configparser import ConfigParser
from ast import literal_eval
from os.path import join, dirname
from typing import Union


class File:
    """
    Class that is method collector regarding files 
    """

    @staticmethod
    def get_config() -> dict:

        """
        A metod to get configurtios from config.ini
        """
        try:
            config = ConfigParser()
            config.read(join(dirname(__file__), "config.ini"))

            return {
                'teams': tuple(config.get('Teams', 'teams').split(", ")),
                'time':  config.getint('Competition', 'time'),
                'vantage': config.getint('Competition', 'vantage'),
                'derive': config.getint('Competition', 'derive'),
                'solutions': literal_eval(config.get('Solutions', 'solutions')),
                'name_file': config.get('Recording', 'name_file'),
                'directory_recording': config.get('Recording', 'directory_recording')
            }
        except Exception as e:
            showerror(
                "Error", f"Unable to complete configuration.  Details: {str(e)}")
            exit()

    @staticmethod
    def save_data(directory: str, name: str, data: dict):

        """
        A metod to save data in a .txt file
        """

        try:
            with open(join(directory, f"{name}.txt"), "w") as record:
                record.write(str(data))
        except Exception as e:
            showerror(
                "Error", f"An error occurred:, data will be printed in the terminal.  Details: {str(e)}")
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


        #collecting data
        data = File.get_config()

        # teams' names
        self.names_teams = data['teams']


        # genaration timer
        self.total_time = data['time']
        self.timer_seconds = self.total_time
        self.timer_status = 0        
        self.timer_label = Label(self, font=("Helvetica", 18, "bold"))
        self.genarate_clock() 
        
        # setting derive and creation solutions dict
        self.derive = data['derive']
        self.solutions = {i+1: {"xm": solution, "correct": 0, "incorrect": 0,
                                "value": data['vantage']} for i, solution in enumerate(data['solutions'])}
        self.number_of_questions = len(self.solutions)       

        # list point, bonus, n_fulled
        self.list_point = {name: {question+1: {"errors": 0, "status": 0, "jolly": 1, "bonus": 0}
                                  for question in range(self.number_of_questions)} for name in self.names_teams}
        for name in self.names_teams:
            self.list_point[name]["base"] = self.number_of_questions*10
        self.fulled = 0

        # data recording
        self.recording = {name: [(0, 220)] for name in self.names_teams}
        self.name_file = data['name_file']
        self.directory_recording = data['directory_recording']

        del data

        #widget costruction

        self.timer_label.pack()
        self.start_button = Button(
            self, text="Start", command=self.start_clock)
        self.start_button.pack()

        points_label = Frame(self, width=1800, height=600)
        points_label.pack(pady=20)

        # Creazione del canvas all'interno dell'etichetta dei punti
        canvas = Canvas(points_label,  width=1800, height=600, scrollregion=(0, 0, 1800, len(self.names_teams)*26))
        canvas.pack(side="left", expand=True, fill="both")

        # Aggiunta di una barra di scorrimento verticale
        scrollbar = Scrollbar(points_label, command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.config(yscrollcommand=scrollbar.set)

        self.frame_point = Frame(
            canvas, width=1800, height=len(self.names_teams)*26)
        canvas.create_window((0, 0), window=self.frame_point, anchor='nw')


        # Creazione delle etichette per ogni domanda e riga
        for question in range(self.number_of_questions):
            Label(self.frame_point, text=f"{question+1}", width=6, anchor="e", justify="center").grid(column=question + 2, row=0, sticky="ns")

        self.update_entry()

    def update_entry(self):
        """
        Update Labels
        """

        # Clear all widgets in the frame except protected columns
        for widget in self.frame_point.winfo_children():
            if widget.grid_info()['row'] != 0:
                widget.destroy()

        # Create value labels for each question
        for question in self.solutions.keys():
            value_label = Entry(self.frame_point, width=6, bd = 5)
            value_label.insert(0, str(self.point_answer(question)))
            value_label.grid(column=question + 1, row=1, sticky="ns")

        # Populate team points and color-code entries
        for row, frame in enumerate(sorted([(self.total_squad_point(team), team) for team in self.names_teams], key=lambda x: x[0], reverse=True), 2):
            team = frame[1]

            Label(self.frame_point, text=f"{team}: ", anchor="e", width=15).grid(
                column=0, row=row, sticky="ns")

            total_num = Entry(self.frame_point, width=6, bd = 5)
            total_num.insert(0, str(self.total_squad_point(team)))
            total_num.grid(column=1, row=row, sticky="ns")


            for column, question in enumerate(self.list_point[team].keys() - ['base'], 2):
                
                total_num = Entry(self.frame_point, width=6, bd=5)
                total_num.insert(0, self.point_answer_x_squad(team, question, True))

                points = self.point_answer_x_squad(team, question)

                if points < 0:
                    total_num.configure(background="red")
                elif points > 0:
                    total_num.configure(background="green")
                else:
                    total_num.configure(background="white")

                total_num.grid(column=column, row=row, sticky="ns")

    # methods about time and timer label
    def start_clock(self):
        """
        Initaialise the timer and block start buttom
        """
        self.start_button.config(state="disabled")
        self.timer_status = 1
        self.update_timer()

    def genarate_clock(self):
        """
        Generate the clock label
        """
        self.timer_label.config(text=f"Time left: {self.timer_seconds // 3600:02}:{(self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}")

    def update_timer(self):

        """
        Update timer and launch bot 
        """
    
        if self.timer_status == 1:

            if self.timer_seconds > 0:

                self.timer_seconds -= 1
                self.genarate_clock()

                if self.timer_seconds % 60 == 0:
                    Thread(target=self.bot()).start

                self.after(100, self.update_timer)

            elif self.timer_seconds == 0:
                File.save_data(self.directory_recording,
                               self.name_file, self.recording)
                self.timer_status = 2

    def bot(self):

        """
        Increase poits amutomaticaly
        """
        for question in self.solutions.keys():
            if self.solutions[question]['correct'] < self.derive and self.timer_seconds >= 1200:
                self.solutions[question]['value'] += 1

        self.update_entry()

    #methods to submit answer
    def submit_answer(self, selected_team: str, entered_question: int, entered_answer: int):

        """
        the metod to submit an answer
        """
        if self.timer_status == 1:

            # get specific error and jolly status
            errors, status, jolly, bonus = self.list_point[selected_team][entered_question].values(
            )

            # gestion error for physical competitions
            xm, correct, incorrect, value = self.solutions[entered_question].values(
            )

            # if correct
            if entered_answer == xm:
                correct += 1
                status = 1
                bonus = -5*correct+25 if 0 < correct < 5 else 3 if correct == 5 else bonus

                if sum([team['status'] for team in self.list_point[selected_team].values() if 'jolly' in team]) == self.number_of_questions:
                    self.fulled += 1
                    self.list_point[selected_team]['base'] += [50,
                                                               30, 20, 15, 10][min(self.fulled, 5) - 1]

            # if wrong
            elif xm != entered_answer and status == 0:
                errors += 1
                incorrect += 1 if errors == 1 else 0

            # inboxing solutions
            self.solutions[entered_question] = {
                "xm": xm, "correct": correct, "incorrect": incorrect, "value": value}

            # inboxing points
            self.list_point[selected_team][entered_question] = {
                "errors": errors, "status": status, "jolly": jolly, "bonus": bonus}

            self.update_entry()
            
            self.recording[selected_team].append(
                (self.total_time-self.timer_seconds, self.total_squad_point(selected_team)))

    def submit_jolly(self, selected_team: str, entered_question: int):

        """
        the metod to submit a jolly
        """
        # check timer staus
        if self.timer_status == 1 and self.timer_seconds > (self.total_time-600):
            # check if other jolly are been given
            if sum([question['jolly'] for question in self.list_point[selected_team].values() if type(question) is dict]) == self.number_of_questions:
                # adding jolly
                self.list_point[selected_team][entered_question]['jolly'] = 2
                self.update_entry()

    #methods to calculate points
    def point_answer(self, question: int) -> int:

        """
        Return the value of answer
        """
        if question <= self.number_of_questions:
            answer_data = self.solutions[question]
            return int(answer_data['value'] + answer_data['incorrect'] * 2)

    def point_answer_x_squad(self, team: str, question: Union[str, int], jolly_simbol: bool = False) -> Union[int, str]:

        """
        Return the points made a team in a question
        """
        # Check if the team is in the list of teams
        if team in self.names_teams:

            # If the question is "base", return the sum of base points
            if question == "base":
                return self.list_point[team]['base']

            # If the question number is within the total number of questions
            elif question <= self.number_of_questions:
                # Get the points for the specific question
                answer_point = self.list_point[team][question]
                

                # Calculate the output points
                result = ((answer_point['status'] * self.point_answer(question) - answer_point['errors'] * 10 + answer_point['bonus']) * answer_point['jolly']) 
                
                return f"{result} J" if answer_point['jolly'] == 2 and  jolly_simbol else result
 

    def total_squad_point(self, team: str) -> int:

        """
        Return the point of a team
        """
        if team in self.names_teams:
            return sum(self.point_answer_x_squad(team, question) for question in self.list_point[team].keys())


class Arbiter_GUI(Toplevel):

    def __init__(self, main):
        super().__init__(main)
        self.submit_answer_main = main.submit_answer

        # starting artiter's window

        self.title("Arbiter")
        self.geometry("500x210")
        self.resizable(False, False)
        self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

        # craation entry for data

        Label(self, text="Team number:").pack()
        self.selected_team = StringVar()
        self.squadre_entry = Combobox(
            self, textvariable=self.selected_team, values=main.names_teams, state="readonly")
        self.selected_team.set("")
        self.squadre_entry.pack()

        Label(self, text="Question number:").pack()
        self.question_entry = Entry(self)
        self.question_entry.pack()

        Label(self, text="Insert an answer:").pack()
        self.answer_entry = Entry(self)
        self.answer_entry.pack()

        Button(self, text="Submit",
               command=self.submit_answer).pack(pady=15)

    def submit_answer(self):

        """
        The method associated to the button
        """

        try:

            Thread(target=self.submit_answer_main(
                self.selected_team.get(), int(self.question_entry.get()), int(self.answer_entry.get()))).start

        except:
            pass

        self.selected_team.set("")
        self.question_entry.delete(0, 'end')
        self.answer_entry.delete(0, 'end')


class Jolly_GUI(Toplevel):

    def __init__(self, main: classmethod):
        super().__init__(main)

        self.submit_jolly_main = main.submit_jolly


        # starting jolly window
        self.title("Jolly")
        self.geometry("500x160")
        self.resizable(False, False)
        self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

        # creatition entry for data
        Label(self, text="Team number:").pack()
        self.selected_team_jolly = StringVar()
        self.squadre_entry_jolly = Combobox(
            self, textvariable=self.selected_team_jolly, values=main.names_teams, state="readonly")
        self.selected_team_jolly.set("")
        self.squadre_entry_jolly.pack()

        Label(self, text="Question number:").pack()
        self.question_entry_jolly = Entry(self)
        self.question_entry_jolly.pack()

        Button(self, text="Submit",
               command=self.submit_jolly).pack(pady=15)

    def submit_jolly(self):

        
        """
        The method associated to the button
        """

        try:
            Thread(target=self.submit_jolly_main(self.selected_team_jolly.get(), int(
                self.question_entry_jolly.get()))).start

        except:
            pass
        self.selected_team_jolly.set("")
        self.question_entry_jolly.delete(0, 'end')


def main():
    root = Main()
    arbiter = Arbiter_GUI(root)
    jolly = Jolly_GUI(root)
    del root, arbiter

    jolly.mainloop()


if __name__ == "__main__":
    from cProfile import run
    run('main()')
