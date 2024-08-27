from viewer import Viewer

def main():
    # Initialize the Viewer with the path to the CSV file
    viewer = Viewer(data_path='../test/data/F202_2018-06-18.csv')
    viewer.run()

if __name__ == "__main__":
    main()
