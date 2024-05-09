#!/usr/bin/env pypy3
# -*- coding: utf-8 -*-

#GUI
from tkinter import Tk, Toplevel, Canvas, StringVar, Entry, Label
from tkinter.ttk import Frame, OptionMenu, Button, Scrollbar
from tkinter.messagebox import showerror

#os
from sys import exit
from threading import Thread
from functools import lru_cache

# class File
from configparser import ConfigParser
from os import walk
from os.path import join, dirname
from typing import Union, List, Literal, Dict
from pypdf import PdfReader

class File:

    @staticmethod
    def get_config() -> dict:
        try:
            config = ConfigParser()
            config.read(join(dirname(__file__), "config.ini"))
            
            return {
                'teams': config.get('Teams', 'teams').split(", "),
                'time':  config.getint('Competition', 'time'),
                'vantage': config.getint('Competition', 'vantage'),
                'derive': config.getint('Competition', 'derive'),
                'solutions_path': config.get('Pyscraper', 'solutions_path'),
                'data_old_path': config.get('Pyscraper', 'data_old_path'),
                'name_file': config.get('Recording', 'name_file'),
                'directory_recording': config.get('Recording', 'directory_recording')      
            }

        except Exception as e:
            showerror("Error", f"Unable to complete configuration.  Details: {str(e)}")
            exit()

    @staticmethod
    def save_data(directory: str, name: str, data: dict):
        try:
            with open(join(directory, f"{name}.txt"), "w") as record:
                record.write(str(data))
        except Exception as e:
            showerror(
                "Error", f"An error occurred:, data will be printed in the terminal.  Details: {str(e)}")
            print(data)

    class Pyscraper:

        @staticmethod
        def list_pdf(directory: str) -> List[str]:
            try:
                return [join(root, file) for root, _, files in walk(directory) for file in files if file.endswith(".pdf")]
            except Exception as e:
                showerror("Error", f"An error occurred, unable to get old pdf. Details: {str(e)}")
                
        @staticmethod
        @lru_cache
        def pre_analize(pdf_path: str) -> List[str]:
            return ''.join(page.extract_text() for page in PdfReader(pdf_path).pages).split("\n")
            

        @staticmethod
        def analize(directory: str, date: str):
            """
            Analyzes PDF files in the specified directory and extracts relevant information.

            Args:
                directory (str): Path to the directory containing PDF files.
                date (str): Target date for analysis.

            Returns:
                dict: A dictionary containing extracted data.
                    - 'names': List of team names.
                    - 'jolly': List of tuples (team name, question number) for jolly questions.
                    - 'answer': List of tuples (team name, question number, time taken, points earned).
            """
            
            list_answer = {'names': [], 'jolly': [], 'answer': []}
            
            for pdf_path in File.Pyscraper.list_pdf(directory):
                n_question = 0
                
                rows = File.Pyscraper.pre_analize(pdf_path)

                try:
                    rows.remove(" ")
                except ValueError:
                    pass
                    
                if rows[2][-10:] == date:

                    list_answer['names'].append(' '.join(rows[3].split()[2:]))

                    for row in rows:
                    
                        row.strip()
                        
                        if row.startswith("DOMANDA"):
                            n_question += 1                   

                            if row [12:17] == "jolly":
                                list_answer['jolly'].append((list_answer['names'][-1], n_question))
                                
                        elif row.startswith("dopo:"):
                        
                            time_taken = int(row.split("dopo:")[1].split()[0])
                            answer = int(row[-4:])
                            list_answer['answer'].append((list_answer['names'][-1], n_question, time_taken, answer))

            list_answer['answer'].sort(key=lambda d: d[2])
            
            return list_answer

        @staticmethod
        def analize_solution(pdf_path: str, date: bool = False) -> Union[List[int], str]:
            try:
                if date:
                    row = File.Pyscraper.pre_analize(pdf_path)[3]
                    if row.startswith("DATA"):
                        return row[-10:]
                    
                else:
                    return [int(riga[-4:]) for riga in File.Pyscraper.pre_analize(pdf_path) if "DOMANDA" in riga]
                    
            except Exception as e:
                showerror("Error", f"An error occurred, unable to complete configuration. Details: {str(e)}")
                exit()


class Main(Tk):
    def __init__(self):
        # cration Main window

        super().__init__()
        self.title("Competitors")
        self.geometry(f"1850x630")
        self.resizable(False, False)
        self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

        # cration solutions

        data = File.get_config()
        date = File.Pyscraper.analize_solution(data['solutions_path'], True)
        data_old = File.Pyscraper.analize(data['data_old_path'], date)
        
        
        self.solutions = {i+1: {"xm": solution,  "correct": 0, "incorrect": 0, "value": data['vantage']} for i, solution in enumerate(File.Pyscraper.analize_solution(data['solutions_path']))}
       
        self.number_of_questions = len(self.solutions)

        # genaration timer

        self.total_time = data['time']
        self.timer_seconds = self.total_time
        self.timer_status = 0

        # name team, base point, svantge, derive
        self.name_team_real = data['teams']
        self.name_team = self.name_team_real + data_old['names']
            
        self.derive = data['derive']

        # data bot
        
        self.answer = data_old['answer']

        # list point, bonus, n_fulled

        self.list_point = {name: {question+1: {"errors": 0, "status": 0, "jolly": 1, "bonus": 0}
                                  for question in range(self.number_of_questions)} for name in self.name_team}
        for name in self.name_team:
            self.list_point[name]["base"] = [self.number_of_questions*10]

        # load old jolly
        for jolly in data_old["jolly"]:
            self.list_point[jolly[0]][jolly[1]]['jolly'] = 2

        self.fulled = 0

        # data recording
        self.recording = {name: [(0, 220)] for name in self.name_team}
        self.name_file = data['name_file']

        # creation clock

        self.directory_recording = data['directory_recording']
        self.timer_label = Label(self, text=f"Time left: {self.timer_seconds // 3600:02}:{(self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}", font=("Helvetica", 18, "bold"))
        
        del data, data_old
        
        
        self.timer_label.pack()
        self.start_button = Button(
            self, text="Start", command=self.start_clock)
        self.start_button.pack()

        points_label = Frame(self, width=1800, height=600)
        points_label.pack(pady=20)


        # Creazione del canvas all'interno dell'etichetta dei punti
        canvas = Canvas(points_label,  width=1800, height= 600)
        canvas.config(scrollregion=(0,0, 1800, len(self.name_team)*26))
        canvas.pack(side="left", expand=True, fill="both")

        # Aggiunta di una barra di scorrimento verticale
        scrollbar = Scrollbar(points_label, command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.config(yscrollcommand=scrollbar.set )

        self.frame_point = Frame(canvas, width=1800, height=len(self.name_team)*26)
        canvas.create_window((0, 0), window=self.frame_point, anchor='nw')

        # Creazione delle etichette per ogni domanda e riga
        for question in range(self.number_of_questions):
            for row in range(len(self.name_team)):
                # Numero della domanda
                index = Label(self.frame_point, text=f"{question+1}: ", width=3, anchor="e")
                index.grid(
                    column=question * 2 + 2, row=row + 1, sticky="ns")
                if row%2==0:
                    index.configure(background="#59D1FF")

        self.protect_columns = [column*2+2 for column in range(self.number_of_questions) ]
        self.update_entry()
        
    def update_entry(self):
        # Clear all widgets in the frame except protected columns
        for widget in self.frame_point.winfo_children():
            if widget.grid_info()['column'] not in self.protect_columns:
                widget.destroy()

        # Create value labels for each question
        for question in self.solutions.keys():
            value_label = Entry(self.frame_point, width=5)
            value_label.insert(0, str(self.point_answer(question)))
            value_label.grid(column=question * 2 + 1, row=0, sticky="ns")


        # Populate team points and color-code entries
        for row, frame in enumerate(sorted([(self.total_squad_point(team), team) for team in self.name_team], key=lambda x: x[0], reverse=True), 1):
            team = frame[1]
            name = Label(self.frame_point, text=f"{team}: ", anchor="e", width=15)
            name.grid(column=0, row=row, sticky="ns")
            if row % 2 == 1:
                name.configure(background="#59D1FF")

            total_num = Entry(self.frame_point, width=5)
            total_num.insert(0, str(self.total_squad_point(team)))
            total_num.grid(column=1, row=row, sticky="ns")

            team_points = self.list_point[team]
            color_map = {True: "green", False: "red", None: "white"}

            for column, question in enumerate(team_points.keys() - ['base'], 1):
                
                points = self.point_answer_x_squad(team, question)
                
                total_num = Entry(self.frame_point, width=5)
                total_num.insert(0, points)
                
                if points < 0:
                    total_num.configure(background="red")
                elif points > 0:
                    total_num.configure(background="green")
                else:
                    total_num.configure(background="white")

                total_num.grid(column=column * 2 + 1, row=row, sticky="ns")


    def start_clock(self):
        self.start_button.config(state="disabled")
        self.timer_status = 1
        self.update_timer()
        
    def update_timer(self):
        if self.timer_status == 1:

            if self.timer_seconds > 0:

                self.timer_seconds -= 1
                self.timer_label.config(text=f"Time left: {self.timer_seconds // 3600:02}:{(self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}")
                
                if self.timer_seconds % 60 == 0:
                    Thread(target = self.bot()).start
  
                    
                self.after(30, self.update_timer)
                    

            elif self.timer_seconds == 0:
                File.save_data(self.directory_recording,
                               self.name_file, self.recording)
                self.timer_status = 2

    def bot(self):
        for question in self.solutions.keys(): 
            self.solutions[question]['value'] += 1
            
                    
        for answer in self.answer:
            if answer[2] == (self.total_time-self.timer_seconds)//60:
                self.submit_answer(
                    answer[0], answer[1], answer[3])
                self.answer.pop(0)

            else:
                break
            
        self.update_entry()

    
    def submit_answer(self, selected_team: str, entered_question: int, entered_answer: int):
        if self.timer_status == 1:
            # get specific error and jolly status
            errors, status, jolly, bonus = self.list_point[selected_team][entered_question].values()

            # gestion error for physical competitions
            xm, correct, incorrect, value = self.solutions[entered_question].values()

            # if correct
            if xm == entered_answer:
                correct += 1
                status = 1
                bonus = -5*correct+25 if 0 < correct < 5 else 3 if correct == 5 else bonus

                if sum([team['status'] for team in self.list_point[selected_team].values() if 'jolly' in team]) == self.number_of_questions:
                    self.list_point[selected_team]['base'] += [50, 30, 20, 15, 10][min(self.fulled, 5)]
                    self.fulled += 1

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

        # check timer staus
        if self.timer_status == 1 and self.timer_seconds > (self.total_time-600):
            # check if other jolly are been given
            if sum([team['jolly'] for team in self.list_point[selected_team].values() if 'jolly' in team]) == self.number_of_questions:
                # adding jolly
                self.list_point[selected_team][entered_question]['jolly'] = 2
                self.update_entry()          
    def point_answer(self, question: int) -> int:
        if question <= self.number_of_questions:
            answer_data = self.solutions[question]
            return int(answer_data['value'] + answer_data['incorrect'] * 2)
    
    def point_answer_x_squad(self, team: str, question: Union[str, int], jolly_simbol: bool = False) -> Union[int, str]:
        # Check if the team is in the list of teams
        if team in self.name_team:
            # Get the points of the team
            points_squadre = self.list_point[team]
            
            # If the question is "base", return the sum of base points
            if question == "base":
                return sum(points_squadre['base'])
            
            # If the question number is within the total number of questions
            elif question <= self.number_of_questions:
                # Get the points for the specific question
                answer_point = points_squadre[question]
                
                # Calculate the output points
                return ((answer_point['status'] * self.point_answer(question) - answer_point['errors'] * 10 + answer_point['bonus']) * answer_point['jolly'])

    def total_squad_point(self, team: str) -> int:
        if team in self.name_team:
            return sum(self.point_answer_x_squad(team, question) for question in self.list_point[team].keys())


class Arbiter_GUI(Toplevel):

    def __init__(self, main):
        super().__init__(main)

        self.submit_answer_main = main.submit_answer
        self.name_team_real = main.name_team_real

        # starting artiter's window

        self.title("Arbiter")
        self.geometry("500x210")
        self.resizable(False, False)
        self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

        # craation entry for data

        Label(self, text="Team number:").pack()
        self.selected_team = StringVar()
        self.squadre_entry = OptionMenu(
            self, self.selected_team, *self.name_team_real[0], *self.name_team_real)
        self.selected_team.set("")
        self.squadre_entry.pack()

        Label(self, text="Question number:").pack()
        self.question_entry = Entry(self)
        self.question_entry.pack()

        Label(self, text="Insert an answer:").pack()
        self.answer_entry = Entry(self)
        self.answer_entry.pack()

        Button(self, text="Submit",
               command=self.submit_answer).pack(pady= 15)

    def submit_answer(self):
        try:

            Thread(target= self.submit_answer_main(
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
        self.name_team_real = main.name_team_real

        # starting jolly window
        self.title("Jolly")
        self.geometry("500x160")
        self.resizable(False, False)
        self.iconbitmap(join(dirname(__file__), "MathScore.ico"))

        # creatition entry for data
        Label(self, text="Team number:").pack()
        self.selected_team_jolly = StringVar()
        self.squadre_entry_jolly = OptionMenu(
            self, self.selected_team_jolly,*self.name_team_real[0], *self.name_team_real)
        self.selected_team_jolly.set("")
        self.squadre_entry_jolly.pack()

        Label(self, text="Question number:").pack()
        self.question_entry_jolly = Entry(self)
        self.question_entry_jolly.pack()

        Button(self, text="Submit",
               command=self.submit_jolly).pack(pady=15)
    def submit_jolly(self):

        try:
            Thread(target= self.submit_jolly_main(self.selected_team_jolly.get(), int(
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
    main()
