
import pandas as pd
from datetime import date as dt
from flask import Flask, request, render_template, send_file
from io import BytesIO

# Dependencies
# pandas, Flask, xlsxwriter, openpyxl

# Create Flask app
app = Flask(__name__)

# Create Flask app route and define parser function
# When user visits the URL, the request method 'GET' is called,
# and the webpage template is rendered.
# And when the user clicks on the form button,
# the request method 'POST' is called,
# which processes any user data pasted to the form textarea.
@app.route('/', methods=['GET', 'POST'])
def parser():
    # Process user data, if the request method is 'POST'
    if request.method == 'POST':
        #Get user input from multiline text form
        user_input = request.form['user_input']
        
        # Process user input.
        # Check to see if line endings are CRLF or LF, 
        # then split the file by line endings.
        # Save pre-processed data to a list and
        # assign list to a new variable, input_text.
        if "\r\n" in user_input:
            input_text = user_input.split('\r\n')
        else:
            input_text = user_input.split('\n')

        # Create initial DataFrame, then process data from list.
        timeEntry = []
        mileageDF = pd.DataFrame(columns=['branch', 'time_in', 'date_in', 'time_out',
                                          'date_out', 'duration', 'length'])

        # Parse data
        for line in input_text:
            # remove any tab or newline from line
            line = line.replace('\t', '')
            line = line.replace('\n', '')

            # skip invalid data and blank lines
            if line in ['CST', '', '-']:
                continue

            # Append each line to timeEntry list until it contains
            # a complete entry; then the entry is added to DataFrame.

            # The last line, and only the last line, in each entry always 
            # contains the word 'miles'.
            # Therefore, we check if 'miles' in line; 
            # then we check if the entire entry is valid, 
            # where if it has 7 items in the list, then it is valid.
            # If not, we reject the entire entry and move on.
            if 'miles' in line:
                timeEntry.append(line)

                if len(timeEntry) == 7:
                    mileageDF.loc[len(mileageDF)] = timeEntry
                    timeEntry.clear()
                else:
                    # Ignoring invalid entry
                    timeEntry.clear()
                    continue
            else:
                timeEntry.append(line)

        # Clean data

        # Combine date and time columns, then convert to datetime format
        mileageDF['datetime_in'] = pd.to_datetime((mileageDF['date_in'] + ' ' + mileageDF['time_in']),
                                                  format='%b %d, %Y %I:%M %p')
        mileageDF['datetime_out'] = pd.to_datetime((mileageDF['date_out'] + ' ' + mileageDF['time_out']),
                                                   format='%b %d, %Y %I:%M %p')

        # Change date format to remove the commas
        for col in ['date_in', 'date_out']:
            mileageDF[col] = pd.to_datetime(mileageDF[col], format='%b %d, %Y')
            mileageDF[col] = mileageDF[col].dt.strftime('%Y-%m-%d')

        for col in ['time_in', 'time_out']:
            mileageDF[col] = pd.to_datetime(mileageDF[col], format='%I:%M %p')
            mileageDF[col] = mileageDF[col].dt.strftime('%I:%M %p')

        # Remove rows where duration = '0:00'
        # This prevents unwanted entries (auto check-in/out when driving by a location)
        mileageDF = mileageDF.loc[mileageDF['duration'] != '0:00']

        # sort rows by date and time
        mileageDF = mileageDF.sort_values(by='datetime_in')
        mileageDF.reset_index(drop=True, inplace=True)

        # Determine actual mileage

        # Get list of unique dates from DataFrame
        uniqueDates = mileageDF['date_in'].unique()

        # Timeero does not accurately calculate the mileage between locations.
        # Therefore, Mileage Chart (contains updated mileage for all locations) 
        # from Finance Office will be referenced and the correct mileage will
        # be generated on the final report.

        # Create DataFrame for final report and
        # enter correct mileage for each location
        finalDF = pd.DataFrame(columns=['Date', 'From Branch', 'To Branch', 'Distance'])
        from_branch = ''
        to_branch = ''
        distance = 0.0

        # create dictionary of library locations for conversion
        conv_dict = {'Main Library': 'MAIN',
                     'Birmingham Branch': 'BIRM',
                     'Heatherdowns Branch': 'HED',
                     'Holland Branch': 'HOLL',
                     'Kent Branch': 'KENT',
                     'Mobile Services': 'KINGRD',
                     'King Road Branch': 'KINGRD',
                     'Lagrange Branch': 'LAG',
                     'Locke Branch': 'LOCKE',
                     'Maumee Branch': 'MAUM',
                     'Mott Branch': 'MOTT',
                     'Oregon Branch': 'OREG',
                     'Friends of the Library': 'WAREHOUSE',
                     'Point Place Branch': 'PTPL',
                     'Reynolds Corners Branch': 'RC',
                     'Sanger Branch': 'SANG',
                     'South Branch': 'SOUTH',
                     'Sylvania Branch': 'SYLV',
                     'Toledo Heights Branch': 'TH',
                     'Washington Branch': 'WASH',
                     'Waterville Branch': 'WATV',
                     'West Toledo Branch': 'WTOL',
                     'Cherry Street Mission': 'MAIN'}

        # Create DataFrame for mileage chart
        chartDF = pd.read_csv('mileage-chart.csv')
        chartDF = chartDF.set_index('LOCATION')


        # Function returns correct mileage from Mileage Chart.
        def get_mileage(from_loc, to_loc):
            from_conv = conv_dict[from_loc]
            to_conv = conv_dict[to_loc]
            return chartDF.loc[from_conv][to_conv]


        # Take entries for each date and calculate starting and ending mileage for each
        # location on that date. Generate data for final report.
        for date in uniqueDates:
            selected_rows = mileageDF.loc[mileageDF['date_in'] == date]

            sr_len = len(selected_rows)

            if sr_len != 1:
                for x in range(0, sr_len):
                    if x == 0:
                        continue
                    elif x == 1:
                        # print(selected_rows)
                        from_branch = selected_rows.iloc[0, 0]
                        to_branch = selected_rows.iloc[1, 0]

                        if from_branch != to_branch:
                            distance = get_mileage(from_branch, to_branch)

                            if distance == 0.00:
                                continue

                            finalDF.loc[len(finalDF.index)] = [date, from_branch,
                                                               to_branch, distance]
                    else:
                        from_branch = to_branch
                        to_branch = selected_rows.iloc[x, 0]

                        if from_branch != to_branch:
                            distance = get_mileage(from_branch, to_branch)

                            if distance == 0.00:
                                continue

                            finalDF.loc[len(finalDF.index)] = [date, from_branch,
                                                               to_branch, distance]
        
        # Save the processed data to an Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            finalDF.to_excel(writer, index=False, freeze_panes=(1, 0))

        # Set the file pointer to the beginning
        output.seek(0)
        
        # Send the file for user to download and save
        filename = "final-mileage-" + dt.today().strftime("%Y-%m-%d") + ".xlsx"
        return send_file(output, download_name=filename, as_attachment=True)

    # Render the form template if the request method is 'GET'
    return render_template('index.html')


# Run app
if __name__ == '__main__':

    app.run(host='0.0.0.0')