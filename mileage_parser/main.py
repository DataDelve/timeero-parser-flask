
import pandas as pd
from datetime import date as dt
from flask import Flask, request, render_template, send_file
from io import BytesIO
from mparser import mparser

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
def main():
    # Process user data, if the request method is 'POST'
    if request.method == 'POST':
        #Get user input from multiline text form
        user_input = request.form['user_input']
        
        # Parse the data
        finalDF = mparser(user_input, False)
        
        # Export final report
        
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
