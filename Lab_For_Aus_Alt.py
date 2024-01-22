from io import BytesIO

import cv2
import pytesseract
import re
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import numpy as np
from datetime import datetime, timedelta
import mimetypes


from dateutil.relativedelta import relativedelta
from passporteye import read_mrz, mrz

# Path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\vlads\Tesseract2\tesseract.exe'


print(pytesseract.image_to_string(Image.open(r'C:\Users\vlads\test\AusPhoto7.jpg')))



def process_string(input_string):
    parts = input_string.split(' ', 0)


    if len(parts) > 1 and parts[1].isspace():
        return parts[0]
    else:
        return input_string





def find_index_of_phrase(lines, phrase):
    for i, line in enumerate(lines):
        if phrase in line:
            return i
    return -1


# Function to extract the name and surname in English from a passport image using Tesseract OCR
def extract_name_and_surname(image_path):

    #mime_type, _ = mimetypes.guess_type(image_path)

    #if mime_type == 'application/pdf':
    doc = fitz.open(image_path)
    page = doc[0]
    pix = page.get_pixmap()
    img_data = pix.tobytes("jpg")
    img = Image.open(BytesIO(img_data))
    img = np.array(img)

    #elif mime_type in ['image/png', 'image/jpeg']:
        #img = cv2.imread(image_path)



    # Load the image using OpenCV
    #img = cv2.imread(image_path)

    # Convert the image to grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)



    binary_img = cv2.adaptiveThreshold(
        gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Perform OCR using Tesseract
    extracted_text = pytesseract.image_to_string(gray_img) #, config='--psm 6'

    # Split the extracted text into lines
    lines = extracted_text.split('\n')

    name = ""
    surname = ""
    nationality = ""
    birth = ""
    sex = ""

    i = 0




    mrz = read_mrz(image_path)

    print(mrz)

    mrz_data = mrz.to_dict()

    print(mrz_data)

    name = re.split(r'\s{2,}', mrz_data['names'])[0]
    surname = re.split(r'\s{2,}', mrz_data['surname'])[0]
    nationality = mrz_data['nationality']



    year_b = int(mrz_data['date_of_birth'][:2])
    month_b = int(mrz_data['date_of_birth'][2:4])
    day_b = int(mrz_data['date_of_birth'][4:])

    current_century = datetime.now().year // 100 * 100
    formatted_date = datetime(year_b + current_century, month_b, day_b)
    formatted_string = formatted_date.strftime("%d/%m/%y")

    birth = formatted_string


    number = mrz_data['personal_number']


    sex = mrz_data['sex']


    year_i = int(mrz_data['expiration_date'][:2])
    month_i = int(mrz_data['expiration_date'][2:4])
    day_i = int(mrz_data['expiration_date'][4:])


    formatted_date_i = datetime(year_i + current_century, month_i, day_i)
    formatted_string_i = formatted_date_i.strftime("%d/%m/%y")

    issue = formatted_string_i

    issue_date = datetime.strptime(issue, "%d/%m/%y")

    start_date = None


    cv2.imshow('Binary Image', binary_img)

    #ten_years = timedelta(days=366 * 10)

    #five_years = timedelta(days=365 * 5)

    print(nationality)

    if nationality in ['ALB', 'DZA', 'AND', 'RUS', 'UKR']:
        start_date = (issue_date - relativedelta(years=10)).strftime("%d/%m/%y")

        #start_date = start_date.strftime("%d/%m/%y")
        print(start_date)

    if nationality in ['PRT', 'IRN', 'TUN']:
        start_date = (issue_date - relativedelta(years=5)).strftime("%d/%m/%y")

        #start_date = start_date.strftime("%d/%m/%y")
        print(start_date)

    return name, surname, gray_img, nationality, birth, sex, issue, start_date, number


# Function to extract information from PDF (Wohnort)
def extract_info_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[1]  # Assuming the information is on the second page

    # Convert the PDF page to an image
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    extracted_text = pytesseract.image_to_string(img, config='--psm 6')

    # Split the extracted text into lines
    lines = extracted_text.split('\n')

    i = 0

    while i < len(lines):
        print(lines[i])
        i = i + 1


    # Function to extract the last word or digit from a string
    def extract_last_word_or_digit(line):
        words_digits = re.findall(r'\b(\w+|\d+)\b', line)
        return words_digits[-1] if words_digits else "Not found"

    # Extract the last word or digit from each line
    postleizeit = extract_last_word_or_digit(lines[1])
    wohnort = extract_last_word_or_digit(lines[2])
    strasse = extract_last_word_or_digit(lines[3])
    hausnummer = extract_last_word_or_digit(lines[4])

    if wohnort == "Pass":
        wohnort = "Passau"

    # Convert Pillow image to NumPy array
    img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # Display the image
    display_image(img_np)

    return postleizeit, wohnort, strasse, hausnummer, doc



def extract_immatrikulation(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]  # Assuming the information is on the first page

    # Extract text from the PDF page
    extracted_text = page.get_text()

    # Split the extracted text into lines
    lines = extracted_text.split('\n')

    #address = ""

    for i, line in enumerate(lines):
        if lines[i] == "Herr" or lines[i] == "Frau":
            #print(lines[i])
            name, surname = lines[i + 1].split()
        #print(i, "   ", line)

        if lines[i] == "geboren am":
            date_birth = lines[i + 1]

        if lines[i] == "geboren in":
            city = lines[i + 1]

        if lines[i] == "wohnhaft in":
            j = find_index_of_phrase(lines, "ist an der")
            address = lines[i + 1]
            i = i + 2
            while i < j:
                address = address + ", " + lines[i]
                i = i + 1




        if lines[i] == "Vorlesungsende":
            semester_ends = lines[i + 1]

    #name = lines[6]
    #date_birth = lines[10]
    #city = lines[12]
    #address = lines[16]

    return name, surname, date_birth, city, address, semester_ends, doc


def extract_health(pdf_path):

    name = ""
    surname = ""
    krankenkasse = ""
    date = ""

    doc = fitz.open(pdf_path)
    page = doc[0]

    extracted_text = page.get_text()

    lines = extracted_text.split('\n')

    full_name = ""

    i = 0

    print(len(lines))

    while i < len(lines):

        #print(i)

        print(lines[i])

        #full_name = ""
        if lines[i] == "Herrn" or lines[i] == "Frauen":
            full_name = lines[i + 1]
            name_parts = full_name.split()
            name = name_parts[0]
            surname = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ""
            #print(full_name)


        #print(name_parts)


        #print(name)
        #print(surname)

        if "Techniker Krankenkasse" in lines[i]:
            krankenkasse = "Techniker Krankenkasse"


        if "gern bestätigen wir Ihnen" in lines[i]:
            match = re.search(r'dem(.*?)bei', lines[i])

        if "gern bestätigen wir" in lines[i]:
            print("Here")
            match = re.search(r'dem(.*?)bei', lines[i])
            date = match.group(1).strip()
            #print(date)


        i = i + 1

    return name, surname, krankenkasse, date, doc






def extract_health1(image_path):

    img = cv2.imread(image_path)

    # Convert the image to grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Perform OCR using Tesseract
    extracted_text = pytesseract.image_to_string(gray_img)

    # Split the extracted text into lines
    lines = extracted_text.split('\n')

    date_pattern = re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b')

    max_similarity = 0
    time = ""

    kassen = ""

    i = 0

    possible_kasse = ["TK", "Techniker"]

    while i < len(lines):
        current_line = lines[i]
        print(current_line)

        if lines[i] == "Geschatszeichen":
            time = lines[i + 2]


        for kasse in possible_kasse:
            if kasse in current_line:
                kassen = kasse


        i += 1

        #print(time)

    return kassen, time, gray_img



def geld(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]  # Assuming the information is on the first page

    # Extract text from the PDF page
    extracted_text = page.get_text()

    # Split the extracted text into lines
    lines = extracted_text.split('\n')

    for i, line in enumerate(lines):
        print(i, "   ", line)

    gold = lines[7]
    date = lines[0]


    return gold, date, doc

# Function to handle the "Open" button click event
def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.pdf")])

    if file_path:
        # Create a popup window for selecting file type
        popup = tk.Toplevel()
        popup.title("Select File Type")

        # Function to handle the button click and call the corresponding function
        def handle_button_click(file_type):
            popup.destroy()
            if file_type == "Passport":
                name_pass, surname, image, nationality, birth, sex, issue, start_date, number = extract_name_and_surname(file_path)
                display_image(image)
                result_label.config(text=f'Name: {name_pass}\nSurname: {surname}\nNationality: {nationality}\nDate of Birth: {birth}\nSex: {sex}\nDate of issue: {issue}\nStart_date: {start_date}\nPersonal number: {number}')
            elif file_type == "Wohnungbescheinigung":
                postleizeit, wohnort, strasse, hausnummer, doc = extract_info_from_pdf(file_path)
                result_label.config(text=f'Postleizeit: {postleizeit}\nWohnort: {wohnort}\nStraße: {strasse}\nHausnummer: {hausnummer}')
                # Close the PDF document when done
                doc.close()
            elif file_type == "Immutriculation":
                name_imm, surname_imm, date, city, address, semester_ends, doc = extract_immatrikulation(file_path)
                result_label.config(text=f'Name: {name_imm}\nSurname: {surname_imm} \n semester ends: {semester_ends} \nDate of birth: {date}\n\nAddress: {address}\nCity of birth: {city}')
                doc.close()
            elif file_type == "Kranken":
                name, surname, krankenkasse, date, doc = extract_health(file_path)
                #display_image(image)
                result_label.config(text=f'name: {name}\nsurname: {surname}\nkrankenkasse: {krankenkasse}\ndate: {date}\n')
                doc.close()
            elif file_type == "Geld":
                gold, date, doc = geld(file_path)
                result_label.config(text=f'Money: {gold}\nDate of amount: {date}\n')
                doc.close





        # Create buttons in the popup window
        passport_button = tk.Button(popup, text="Passport", command=lambda: handle_button_click("Passport"))
        passport_button.pack()

        wohnung_button = tk.Button(popup, text="Wohnungbescheinigung", command=lambda: handle_button_click("Wohnungbescheinigung"))
        wohnung_button.pack()

        immutriculation_button = tk.Button(popup, text="Immutriculation", command=lambda: handle_button_click("Immutriculation"))
        immutriculation_button.pack()

        kranken_button = tk.Button(popup, text="Kranken", command=lambda: handle_button_click("Kranken"))
        kranken_button.pack()

        geld_button = tk.Button(popup, text="Geld", command=lambda: handle_button_click("Geld"))
        geld_button.pack()







# Function to display the image in the Tkinter window
def display_image(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(img)

    # Update the panel with the new image
    panel.img = img
    panel.config(image=img)


# Create the main application window
app = tk.Tk()
app.title("Passport OCR")

# Create a button for opening files
open_button = tk.Button(app, text="Open File", command=open_file)
open_button.pack()

# Create a label to display the result
result_label = tk.Label(app, text="")
result_label.pack()

# Create a panel to display the image
panel = tk.Label(app)
panel.pack()

app.mainloop()