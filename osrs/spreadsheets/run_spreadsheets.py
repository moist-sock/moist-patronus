from toa_google_sheet import main as toa_spreadsheet
from google_sheet_inputter import inputter


def main():
    inputter("The Whisperer", "whisperer kc", compare_rank=1)
    inputter("The Leviathan", "leviathan kc", compare_rank=1, main="hemeonc")
    inputter("Duke Sucellus", "duke kc", extra="hemeonc", compare_rank=1000)
    toa_spreadsheet()


if __name__ == '__main__':
    main()
