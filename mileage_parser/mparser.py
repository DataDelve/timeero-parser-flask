
import pandas as pd

# Pass the timeero data in string format;
# and specify True, if the function should return raw data
# or False, for the Final clean data that includes correct mileage.
# ie. mparser(timeero_data, True)

def mparser(user_input, raw_data):
    # %% [1] Parse data and create initial dataframe

    timeEntry = []
    dataDF = pd.DataFrame(columns=['branch', 'time_in', 'date_in', 'time_out', 
                                    'date_out', 'duration', 'length'])

    # Process user input.
    # Check to see if line endings are CRLF or LF, 
    # then split the file by line endings.
    # Save pre-processed data to a list, input_text.
    
    if "\r\n" in user_input:
        input_text = user_input.split('\r\n')
    else:
        input_text = user_input.split('\n')

    for line in input_text:
        # remove tab and newline from line
        line = line.replace('\t', '')
        line = line.replace('\n', '')
        
        # remove invalid data and blank lines
        if line in ['CST', '', '-']:
            continue
        
        # The last line in each entry always contains the word 'miles'.
        # Therefore, we check if 'miles' in line; then we check if the entire entry
        # is valid, where if it has 7 items in the list, then it is valid.
        # If not, we reject the entire entry and move on.
        
        if "miles" in line:
            timeEntry.append(line)
            
            if len(timeEntry) == 7:
                dataDF.loc[len(dataDF)] = timeEntry
                timeEntry.clear()
            else:
                timeEntry.clear()
                continue
        else:
            timeEntry.append(line)

    # Export raw data, if raw_data == True
    if raw_data == True:
        return dataDF        

    # %% [2] Clean data

    # combine date and time columns, then convert to datetime format
    dataDF['datetime_in'] = pd.to_datetime((dataDF['date_in'] + ' ' + dataDF['time_in']),
                                            format='%b %d, %Y %I:%M %p')
    dataDF['datetime_out'] = pd.to_datetime((dataDF['date_out'] + ' ' + dataDF['time_out']),
                                            format='%b %d, %Y %I:%M %p')

    # Change date format to remove the commas
    for col in ['date_in', 'date_out']:
        dataDF[col] = pd.to_datetime(dataDF[col], format='%b %d, %Y')
        dataDF[col] = dataDF[col].dt.strftime('%Y-%m-%d')

    for col in ['time_in', 'time_out']:
        dataDF[col] = pd.to_datetime(dataDF[col], format='%I:%M %p')
        dataDF[col] = dataDF[col].dt.strftime('%I:%M %p')

    # Remove rows where duration = '0:00'
    dataDF = dataDF.loc[dataDF['duration'] != '0:00']

    # sort rows by date and time
    dataDF = dataDF.sort_values(by='datetime_in')
    dataDF.reset_index(drop=True, inplace=True)

    # %% [3] Determine actual mileage

    # Get list of unique dates from dataframe
    uniqueDates = dataDF['date_in'].unique()

    # Timeero does not accurately calculate the mileage between locations.  
    # Therefore, Mileage Chart (contains updated mileage for all locations) will be 
    # referenced and the correct mileage will be generated on the final report.

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

    # Enter correct mileage for each location
    finalDF = pd.DataFrame(columns=['Date', 'From Branch', 'To Branch', 'Distance'])
    from_branch = ''
    to_branch = ''
    distance = 0.0

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
        selected_rows = dataDF.loc[dataDF['date_in'] == date]

        sr_len = len(selected_rows)

        if sr_len != 1:
            for x in range(0, sr_len):
                if x == 0:
                    continue
                elif x == 1:
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

    return finalDF
