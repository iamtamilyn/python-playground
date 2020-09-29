# from tkinter import * 
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
import os
import pyodbc
import time
import datetime

# Set Window
window = tk.Tk()
window.title("WATT")
window.geometry('700x400')
window.iconbitmap('watticon.ico')
window.grid_rowconfigure(0,weight=1)
window.grid_columnconfigure(0,weight=1)


def query_database(sqlStatement):
    # print('DB Executing',sqlStatement)
    global conn
    conn = pyodbc.connect(serverString)
    cursor = conn.cursor()
    cursor.execute(sqlStatement)
    results = []
    try: 
        for row in cursor:
            results.append(row)
    except:
        results = None
    # print('DB Return:',results)
    conn.commit()
    conn.close()
    return results


def get_tasktype_list():
    # get list of task types for combo box
    global taskTypes
    global taskTypesDict
    taskTypes = query_database("SELECT taskTypeId, taskTypeName FROM watt.taskType")
    taskTypesDict = dict(taskTypes)
    taskTypes = []
    # for value in taskTypesDict.values():
    #     taskTypes.append(value)
    # tasklist_combo['values']= taskTypes
    # tasklist_combo.current(0)


def set_tasktype_list():
    # set list of task types for combo box
    for value in taskTypesDict.values():
        taskTypes.append(value)
    tasklist_combo['values']= taskTypes
    tasklist_combo.current(0)


def set_worked_list():
    worked_list = query_database("SELECT taskTypeName,clientCode,workedItemNote,totalMinutesWorked,totalHoursWorked FROM watt.V_dailyWorkTrackedByTask  ORDER BY  lastStart DESC")
    # delete level 2 items
    current_list = tree.get_children(tree_level2)
    try:
        for item in current_list:
            tree.delete(item)
    # item not found?
    except:
        print('item not found')
        pass
    # Format and Insert - first col to text, rest to values
    for item in worked_list:
        task = item[0]
        values_list = item[1:]
        tree.insert(tree_level2,"end", text=task,values=values_list, tag='row')
        

def set_timer():
    # set start time of the timer
    global startTime
    startTime = time.time()
    update_timer()


def update_timer():
    # continually calculate the time since the start time of the timer
    updatedTime = time.time()
    duration = updatedTime - startTime # seconds
    duration = time.strftime('%H:%M:%S', time.gmtime(duration) )
    timerLabel.configure(text=duration)
    window.after(1000, update_timer)


def stop_timer():
    global startTime
    startTime = time.time()
    timerLabel.configure(text="")
    update_timer()
    

def tasktype_selected(event):
    # show selected task
    tasktype_name = tasklist_combo.get()
    status_label.configure(text = tasktype_name)
    print(taskTypesDict)
    print(list(taskTypesDict.keys())[list(taskTypesDict.values()).index(tasktype_name)])


def get_id_of_selected_tasktype(tasktype_name):
     # error if no task type selected
    if tasktype_name == "":
        # messagebox.showinfo('Error: Missing Selection','Choose a Task Type')
        return
    taskTypeId = list(taskTypesDict.keys())[list(taskTypesDict.values()).index(tasktype_name)]
    return taskTypeId


def start_work_item():
    global currentWorkingItemId
    # Info for Working Item to Start
    clientCode = clientCodeTxt.get()
    workingNote = workedItemNote.get()
    startDateTime = time.strftime("%Y-%m-%d %H:%M:%S")
    tasktype_name = tasklist_combo.get()
    taskTypeid = get_id_of_selected_tasktype(tasktype_name) # Get Task Id
    # Exit of No Item Selected
    if taskTypeid == None:
        messagebox.showinfo('Error: Missing Selection','Choose a Task Type')
        return

    # check for working item in progress to end
    print(tree.get_children(tree_level1))
    if tree.get_children(tree_level1) != ('0',):
        end_work_item()

    # Insert Working Item
    sqlStatement = "INSERT INTO watt.worked (taskTypeId,clientCode,workedItemNote, startedAtTime) VALUES (" + str(taskTypeid) + ",'" + clientCode + "','" + workingNote + "','" + startDateTime + "')"
    query_database(sqlStatement)

    # Information on Working Item
    sqlStatement = 'SELECT workedItemId,taskTypeHexColor AS lastEntry FROM watt.worked INNER JOIN watt.tasktype ON worked.taskTypeId = taskType.taskTypeId WHERE workedItemId = (SELECT MAX(workedItemId) AS lastEntry FROM watt.worked)'
    results = []
    results = query_database(sqlStatement)
    currentWorkingItemId = results[0][0]
    # setColor = '#' + results[0][1]

    status_label.configure(text= "Added Item!")
    set_timer()
    # set working item
    endButton.grid(column=4, row=2,sticky="nsew",pady=3,padx=1)
    tasklist_combo.current()
    # tree insert, remove spacer (1)
    set_progress_item(1)
    tree.insert(tree_level1,1, text=tasktype_name,values=(clientCode,workingNote), tags ='progress')
    # clear text fields
    clientCodeTxt.delete(0, "end")
    clientCodeTxt.insert(0, "")
    workedItemNote.delete(0, "end")
    workedItemNote.insert(0, "")


def end_work_item():
    endDateTime = time.strftime("%Y-%m-%d %H:%M:%S")
    sqlStatement = "UPDATE watt.worked SET endedAtTime = '" + endDateTime + "' WHERE workedItemId = " + str(currentWorkingItemId)
    # print(sqlStatement)
    query_database(sqlStatement)
    # un-set working item
    timerLabel.configure(text="00:00:00")
    status_label.configure(text= "Ended Item!")
    # tree item delete and add spacer (0)
    set_progress_item(0)
    # Hide End Button
    endButton.grid_forget()
    # Stop Timer
    stop_timer()
    #Update Report
    set_worked_list()

def set_progress_item(new_item):
    if new_item == 0:
        if tree.get_children(tree_level1) != ('0',):
            tree.delete(tree.get_children(tree_level1))
        tree.insert(tree_level1,1, 0, text='',values=('',''), tags ='progress')
    elif new_item == 1:
        tree.delete(tree.get_children(tree_level1))


def before_exit():
    if tree.get_children(tree_level1) != ('0',):
        end_work_item()
    window.destroy()


def Tree_OnDoubleClick(event):
    item = tree.selection()[0]
    itemvalues = tree.item(item,"value")
    # if item = "Previous Today" or "In Progress" then exit
    if tree.item(item,"text") == "Previous Today" or tree.item(item,"text") == "In Progress":
        exit
    print("you clicked on", tree.item(item,"text"),tree.item(item,"value") )
    # update selections
    clientCodeTxt.delete(0, "end")
    clientCodeTxt.insert(0, itemvalues[0])
    workedItemNote.delete(0, "end")
    workedItemNote.insert(0, itemvalues[1])
    tasklist_combo.current(list(taskTypesDict.keys())[list(taskTypesDict.values()).index(tree.item(item,"text"))]-1)
    

def create_tracking_frame():
    global tasklist_combo
    # global workingTaskTypeLabel
    # global workingClientCodeLabel
    # global workingTaskNoteLabel
    global timerLabel
    global status_label
    global endButton
    global clientCodeTxt
    global workedItemNote
    global tree, tree_level1, tree_level2

    # Frames
    tracking_frame = tk.Frame(window, bg=color_back, height=100)
    tracking_frame.grid(column=0,row=0,sticky='nesw',padx=5,pady=5)
    tracking_frame.grid_columnconfigure(0,weight=1)
    tracking_frame.grid_columnconfigure(1,weight=1)
    tracking_frame.grid_columnconfigure(2,weight=1)
    tracking_frame.grid_columnconfigure(3,weight=1)
    tracking_frame.grid_columnconfigure(4,weight=1)
    tracking_frame.grid_rowconfigure(0,weight=1)
    tracking_frame.grid_rowconfigure(1,weight=1)
    tracking_frame.grid_rowconfigure(2,weight=1)
    tracking_frame.grid_rowconfigure(3,weight=1)
    title_frame = tk.Frame(tracking_frame, bg=color_header)
    title_frame.grid(column=0,row=0,columnspan=6, sticky='ew')
    
    # Row 0 (messages)
    status_label = tk.Label(title_frame,text="Hello, " + username +"! Start Tracking", font=("Calibri Bold", standard_font), bg=color_header, fg=color_header_fg)
    status_label.grid(column=0, row=1,pady=5,columnspan=5)
    # Row 1 (Headers)
    taskListLabel = tk.Label(tracking_frame,text="Task Type", font=("Calibri Bold", standard_font))
    taskListLabel.grid(column=0,row=1,sticky="nsew",pady=3,padx=1)
    clientCodeLabel = tk.Label(tracking_frame,text="Client Code", font=("Calibri Bold", standard_font), width=10)
    clientCodeLabel.grid(column=1,row=1,sticky="nsew",pady=3,padx=1)
    workedItemNoteLabel = tk.Label(tracking_frame,text="Note", font=("Calibri Bold", standard_font))
    workedItemNoteLabel.grid(column=2,row=1,sticky="nsew",pady=3,padx=1)
    timer_label = tk.Label(tracking_frame,text="Timer:", font=("Calibri Bold", standard_font), width=12)
    timer_label.grid(column=3,row=1,sticky="nsew",pady=3,padx=0)
    timerLabel = tk.Label(tracking_frame, text="", font =("Calibri", standard_font),width=11)
    timerLabel.grid(column=4,row=1,sticky="nsew",pady=3,padx=0)
    # Row 2 (Entry)
    tasklist_combo = ttk.Combobox(tracking_frame, font ="Calibri 9",width=25,height=25)
    tasklist_combo.bind("<<ComboboxSelected>>", tasktype_selected)
    clientCodeTxt = tk.Entry(tracking_frame,font ="Calibri 10",width=10)
    workedItemNote = tk.Entry(tracking_frame,font ="Calibri 10",width=20)
    startButton = tk.Button(tracking_frame, text="Start",font ="Calibri 9", command=start_work_item, width=15)
    tasklist_combo.grid(column=0, row=2,sticky="nsew",pady=3,padx=1)
    clientCodeTxt.grid(column=1,row=2,sticky="nsew",pady=3,padx=1)
    workedItemNote.grid(column=2,row=2,sticky="nsew",pady=3,padx=1)
    startButton.grid(column=3, row=2,sticky="nsew",pady=3,padx=1)
    endButton = tk.Button(tracking_frame, text="End",font ="Calibri 9", command=end_work_item, width=15)
    endButton.grid(column=4, row=2,sticky="nsew",pady=3,padx=1)
    endButton.grid_forget()

    # Row 3 (Previous Options)
    # workedListBox = tk.Listbox(tracking_frame)
    # workedListBox.grid(column=0,row=4,sticky="nsew",columnspan=3)

    tree = ttk.Treeview(tracking_frame)
    tree["columns"] = ("one","two","three","four")
    tree.column("#0",width=200,minwidth=200, stretch=tk.NO)
    tree.column("one",width=50,minwidth=50, stretch=tk.NO)
    tree.column("two",width=80,minwidth=80, stretch=tk.NO)
    tree.column("three",width=40,minwidth=40, stretch=tk.NO)
    tree.column("four",width=70,minwidth=70, stretch=tk.NO)
    tree.heading("#0",text="Task",anchor=tk.W)
    tree.heading("one",text="Code",anchor=tk.W)
    tree.heading("two",text="Ticket",anchor=tk.W)
    tree.heading("three",text="Mins",anchor=tk.W)
    tree.heading("four",text="Hours",anchor=tk.W)
    # tree.insert("", "end","", values=("","Task","CODE","CLDS-1234"))
    # Level 1
    tree.tag_configure('progress', background='#DFDFDF', foreground='black', font=('Arial',11))
    tree.tag_configure('report', background='#DFDFDF')
    tree_level1 = tree.insert("", 1,"Active", text="In Progress", values=("","",""), tags ='progress')
    tree_level2 = tree.insert("", 2,"Previous", text="Previous Today", values=(" "," ",""), tags ='report')
    tree.item("Active", open=True)
    tree.item("Previous", open=True)
    # # Level 2
    tree.insert(tree_level1,1, 0, text='',values=('',''), tags ='progress')
    # tree.insert(folder1, "end",text="photo1.png", values=("23-Jun-17 11:28","PNG file","2.6 KB"))
    # tree.insert(folder1, "end", text="photo2.png", values=("23-Jun-17 11:29","PNG file","3.2 KB"))
    # tree.insert(folder1, "end", text="photo3.png", values=("23-Jun-17 11:30","PNG file","3.1 KB"))
    tree.grid(column=0,row=3,columnspan=4,sticky="nswe")
    tree.bind("<Double-1>", Tree_OnDoubleClick)
    style = ttk.Style()

    style.configure("Treeview", highlightthickness=0, bd=0, font=('Calibri', 9))
    style.configure("Treeview.Heading", font=("Calibri Bold", 12))
    style.configure("Treeview.item", font=("Calibri Bold", 12))
    style.layout("Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})]) # Remove the borders
    vsb = ttk.Scrollbar(tracking_frame, orient="vertical", command=tree.yview)
    vsb.grid(column=4, row=3, sticky="nsw")
    # vbs.configure(command=tree.yview)


def create_reporting_frame():
    # Row 1-len (Report Table Results)
    global widgets

    reporting_frame = tk.Frame(window, bg=color_back,width=300)
    reporting_frame.grid(column=0,row=1,columnspan=6,rowspan=4, sticky='new',padx=5,pady=5)
    reporting_frame.grid_columnconfigure(0,weight=1)
    reporting_frame.grid_columnconfigure(1,weight=1)

    rows = 10
    columns=2
    widgets = []
    for row in range(rows):
        current_row = []
        for column in range(columns):
            if row == 0:
                label = tk.Label(reporting_frame, text="",font=("Calibri Bold", 12), bg=color_header, fg = color_header_fg)
            else:
                label = tk.Label(reporting_frame, text="",bg=color_tile, fg=color_tile_fg)
                # label = tk.Label(window, text="0" % (row, column),borderwidth=0, width=10)
            label.grid(row=row, column=column, sticky="nsew", padx=1, pady=1)
            current_row.append(label)
        widgets.append(current_row)
    # reporting_frame.grid_forget() # DEBUG


def database_connection():
    try:
        sqlStatement = "SELECT * FROM WATT.taskType"
        query_database(sqlStatement)
    except:
        print('no DB here')
        messagebox.showinfo('Error: Missing Database','Closing, Try Again with DB.')
        exit(0)    


#Set Global Variables
username = os.getlogin()
# CONVENTION computername\LOCAL_username
# serverString = 'Driver={SQL Server};Server=SJL-5PPPDC2\\TAPE_LOCAL;Database=WATTapplication;Trusted_Connection=yes'
# serverString = 'Driver={SQL Server};Server=SJL-D6PXX33;Database=WATTapplication;Trusted_Connection=yes'
serverString = 'Driver={SQL Server};Server=' + os.getenv('COMPUTERNAME') + ';Database=WATTapplication;Trusted_Connection=yes'
print(serverString)
standard_font = 12

def color_setting():
    global color_header
    global color_header_fg
    global color_tile
    global color_tile_fg
    global color_back

    sqlStatement = "SELECT activeColorSchemeId FROM WATT.settings"
    results = query_database(sqlStatement)
    schemeId = results[0][0]

    sqlStatement = "SELECT * FROM WATT.colorScheme WHERE schemeId = " + str(schemeId)
    results = query_database(sqlStatement)

    try:
        color_header = results[0][1]
        window.config(background=color_header)
    except:
        color_header = "#702082"

    try:
        color_header_fg = results[0][2]
        window.config(background=color_header_fg)
    except:
        color_header_fg = "#FFFFFF"  

    try:
        color_tile = results[0][3]
        window.config(background=color_tile)
    except:
        color_tile = "#FFFFFF"
        
    try:
        color_tile_fg = results[0][4]
        window.config(background=color_tile_fg)
    except:
        color_tile_fg = "#702082"

    try:
        color_back = results[0][5]
        window.config(background=color_back)
    except: 
        color_back = "#D8D7DF"

    window.config(background=color_back)



# Build Application
database_connection()
color_setting()
create_tracking_frame()
get_tasktype_list()
set_tasktype_list()
set_worked_list()
# create_reporting_frame()
set_timer()
# current_watt()


window.protocol("WM_DELETE_WINDOW", before_exit)
# ongoing loop
window.mainloop()
