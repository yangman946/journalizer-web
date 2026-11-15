'''
Manages journal entries:
* stores entries
* Dates  entries
* encryption/decryption
* directory manager


future features
* backup online
*



SCRAP EVERYTHING....

Actually, by default, every entry WIll be ENCRYPTED...

It will be decrypted and displayed upon request...

But the text file itself is NOT modified

The security will be to input the KEY

A key will be generated based on user preference and On start. 
'''


from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from datetime import datetime
from pathlib import Path
from os import listdir, walk
from os.path import isfile, join
import os
from dotenv import load_dotenv

load_dotenv()


import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class Crypto:
    # responsible for cryptography, etc.
    def __init__(self, password=''):
        """
        try:
            self.key = self.load_key()
            self.cipher_suite = Fernet(self.key)
        except:
            self.write_key()
            self.key = self.load_key()
            self.cipher_suite = Fernet(self.key)
        """
        BASE_DIR = Path(__file__).resolve().parent # this is a temporary file
        
        self.path = BASE_DIR

        self.My_key = Path(f"{self.path}/key.key")

        # temp:
        if self.My_key.is_file():
            file = open(f"{self.path}/key.key", 'rb')
            key_ = file.read()
            self.cipher_suite = Fernet(key_)

        else:
            # require password
            

            if password == '':
                return

            salt = b"unique_static_salt" 

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            password_key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
            self.cipher_suite = Fernet(password_key)
            self.save(key=password_key)

    # short term memory
    def save(self, key):
        with open(f"{self.path}/key.key", "wb") as key_file:
            key_file.write(key)
        
    # delete
    def lock(self):
        path_file = Path(f"{self.path}/key.key")
        path_file.unlink(missing_ok=True)
        
    def checkFile(self):
        return self.My_key.is_file()

    """
    def write_key(self):
        key = Fernet.generate_key()
        with open('key.key', "wb") as key_file:
            key_file.write(key)

    def load_key(self):
        file = open('key.key', 'rb')
        key_ = file.read()
        file.close()
        return key_
    
    """


    # used to encrypt/decrypt everything at once <-- DO THIS ONCE!
    # FOR DEBUG PURPOSES ONLY
    '''
    def Cycle(self, encrypt):
        for root, _, files in walk("journals"):
            for filename in files:
                filepath = join(root, filename)

                with open(filepath, "r", encoding ="utf-8") as f:
                    
                    content = f.readlines()
                    data = [content[0], "".join(content[1:])]

                try:
                    if encrypt:
                        newdata = self.cipher_suite.encrypt(data[1].encode('utf-8'))
                    else:
                        newdata = self.cipher_suite.decrypt(data[1])
                except InvalidToken:
                    print(f"Skipping {filepath}: invalid key or file not encrypted.")
                    continue

                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(content[0])
                    f.write("\n")
                    f.write("\n")
                    f.write(str(newdata))
                    f.flush()

                print(f"Processed {filepath}")
    '''

    # used to encrypt/decrypt only once 
    
    def code(self, data, encrypt):
        try:
            if encrypt:
                Newdata = self.cipher_suite.encrypt(data.encode('utf-8'))
                return Newdata
            else:
                Newdata = self.cipher_suite.decrypt(data)
                return Newdata.decode('utf-8')
        except InvalidToken:
            return None
            
    
            
    



# main class --> will use crypto class to help encrypt/decrypt
class fileManager:
    def __init__(self):
        #self.path = "journals/" # where we store our journals
        
        #self.crypto = Crypto(None)


        self.values = {}
        self.exists = False

        #BASE_DIR = Path(__file__).resolve().parent # C:\Users\Clarence\Documents\GitHub\journalizer-web\journal\services
        self.BASE_DIR = Path(os.environ.get('JOURNAL_PATH')) # path containing journals

        self.path = self.BASE_DIR / "journals"

        if self.path.exists():
            self.exists = True

            #print(self.path)

            for (dirpath, dirnames, filenames) in walk(self.path):

                template = {
                    "folders": dirnames,
                    "entries": filenames
                }
                self.values[dirpath] = template


            # sort the years, months and days
            self.refresh()

    
    def refresh(self):
        for key, value in self.values.items():
            # Sort folders numerically (descending)
            value["folders"].sort(key=int, reverse=True)

            # Sort entries by the number before .txt (descending)
            value["entries"].sort(
                key=lambda x: int(x.removesuffix(".txt")),
                reverse=True
        )

        #print(self.values)


    def saveEntry(self, content):
        now = datetime.now()

        yearx = now.year
        day = now.strftime("%d").lstrip("0")
        month = now.strftime("%m").lstrip("0")
        year = now.strftime("%y")

        formatted_date = f"{day}{month}{year}"

        # Define file path
        file_path = Path(self.path) / str(yearx) / month / f"{formatted_date}.txt"

        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write entry
        with file_path.open("w", encoding="utf-8") as file:
            file.write(f"{day}/{month}/{year}\n\n")
            file.write(content)

        # Refresh directory structure
        self.refresh()

        return yearx, month, formatted_date

    def find(self, yearx, month, formatted_date):

        # Function to read entry based on URL information
        base_path = Path(self.path)

        years = self.values[str(base_path)]["folders"]
        yearind = years.index(str(yearx))

        year_path = str(base_path / str(yearx))
        months = self.values[year_path]["folders"]
        monthind = months.index(str(month))

        month_path = str(base_path / str(yearx) / str(month))
        days = self.values[month_path]["entries"]
        dayind = days.index(f"{formatted_date}.txt")

        # Return content and indices
        return (
            self.getContent(self.getEntry(yearind, monthind, dayind)),
            yearind,
            monthind,
            dayind
        )

    def todayExists(self):
        now = datetime.now()
        
        yearx = now.year
        day = now.strftime("%d").lstrip("0")
        month = now.strftime("%m").lstrip("0")
        year = now.strftime("%y")
        formatted_date = f"{day}{month}{year}"


        #path = f"{self.path}/{yearx}/{month}/{formatted_date}.txt"
        p1 = str(Path(self.path) / str(yearx) / str(month) / str(f"{formatted_date}.txt"))
        p = Path(p1)

        return p.exists()

    def allEntries(self):
        # returns list of all entries since the start of time
        #print(self.values)
        
        filenames = []

        for folder, contents in self.values.items():
            for entry in contents["entries"]:
                filenames.append(entry.removesuffix(".txt"))

        #print(filenames)

        return filenames

    def findEntry(self, name, monthI, yearI):
        # finds entry
        P = str(Path(self.path) / str(yearI) / str(monthI))
        searchDIR = Path(P)
        print(searchDIR)
        file = f"{name}.txt"
        print(file)

        file_path = next(searchDIR.rglob(file), None)

        return file_path




    def date2ind(self, year, month = None, day = None):

        

        # converts date to index
        yind = None
        mind = None
        dind = None

        years = self.values[f"{self.path}"]["folders"]
        year_path = str(Path(self.path) / str(year))
        yind = years.index(str(year))

        if month != None:
            
            months = self.values[year_path]["folders"]
            month_path = str(Path(year_path) / str(month))
            mind = months.index(str(month))

            if day != None:
                days = self.values[month_path]["entries"]
                
                dind = days.index(day)
        return [yind, mind, dind]
        
        

    def getEntry(self, yearind = None, monthind = None, dayind = None):
        # get entry based on indicies
        # if you want to access via date use date2ind 

        if self.exists == False:
            return None
        # returns list of years
        years = self.values[f"{self.path}"]["folders"]
        if yearind == None:
            return years


        # return list of months
        year = years[yearind]
        year_path = str(Path(self.path) / str(year))
        months = self.values[year_path]["folders"]

        if monthind == None:
            return months
        
        # returns list of days
        month = months[monthind]
        month_path = str(Path(year_path) / str(month))
        days = self.values[month_path]["entries"]

        if dayind == None:
            return days

        name = days[dayind]

        # return the file itself
        #file = f"{self.path}/{year}/{month}/{name}"
        return str(Path(month_path) / str(name))


    def getRoot(self):
        return self.values
    

    def getContent(self, path):
        try:
            with open(path, "r", encoding ="utf-8") as file:
                content = file.readlines()
                return [content[0], "".join(content[1:])]
        except:
            return [None, "An error has occured when reading this document"]

        


        

# temporary script to port over existing entries - may be implemented as a feature
class Importer:
    def __init__(self):
        pass

if __name__ == "__main__":
    #app = fileManager()

    # bulk encrypt entries method
    password = input("Password: ")

    if password == input("Confirm Password: "):
        app = Crypto(password)
        app.Cycle(True)

    
