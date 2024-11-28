# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
station = Base.classes.station
measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################

# /
# Start at the homepage.
# List all the available routes.

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start><br/>"
        f"/api/v1.0/&lt;start>/&lt;end><br/>"
    )

# /api/v1.0/precipitation
# Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.
# Return the JSON representation of your dictionary.

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Starting from the most recent data point in the database. 
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    most_recent_date_dt = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')

    # Calculate the date one year from the last date in data set.
    one_year_before_mrd_dt = most_recent_date_dt - dt.timedelta(days = 365)
    one_year_before = dt.datetime.strftime(one_year_before_mrd_dt, '%Y-%m-%d')


    """Return a dictionary of all dates and precipitation"""
    # Query date and prcp data
    results = session.query(measurement.date, measurement.prcp).\
                filter(measurement.date >= one_year_before).\
                filter(measurement.prcp !='').\
                order_by(measurement.date.desc()).all()
    
    session.close()

    # Create a dictionary using date as the key and prcp as the value
    precipitation_dict = {}
    for date, prcp in results:
        precipitation_dict[date] = prcp

    return jsonify(precipitation_dict)


# /api/v1.0/stations
# Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all station names"""
    # Query all station names
    results = session.query(station.station).all()

    session.close()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(results))

    return jsonify(all_stations)


# /api/v1.0/tobs
# Query the dates and temperature observations of the most-active station for the previous year of data.
# Return a JSON list of temperature observations for the previous year.

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of temperature observations for the previous year"""
    
    # Find out the most active station
    most_active_station = session.query(measurement.station).\
                                    group_by(measurement.station).\
                                    order_by(func.count(measurement.id).desc()).first()[0]
    
    ## Starting from the most recent data point in the database. 
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    most_recent_date_dt = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')

    ## Calculate the date one year from the last date in data set.
    one_year_before_mrd_dt = most_recent_date_dt - dt.timedelta(days = 365)
    one_year_before = dt.datetime.strftime(one_year_before_mrd_dt, '%Y-%m-%d')

    # measurement.tobs must not be empty.
    results = session.query(measurement.date, measurement.tobs).\
                        filter(measurement.station == most_active_station).\
                        filter(measurement.date >= one_year_before).\
                        filter(measurement.tobs !='').all()
    session.close()
    
    # Create a dictionary from the row data and append to a list of all_temperatures
    all_temperatures = []
    for date, tobs in results:
        temperatures_dict = {}
        temperatures_dict["date"] = date
        temperatures_dict["tobs"] = tobs
        all_temperatures.append(temperatures_dict)

    return jsonify(all_temperatures)


# /api/v1.0/<start> and /api/v1.0/<start>/<end>
# Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range.
# For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
# For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.

@app.route("/api/v1.0/<start>", defaults={'end': None})



@app.route("/api/v1.0/<start>/<end>")
def start_end_query(start, end):
    sel = [func.min(measurement.tobs),func.avg(measurement.tobs),func.max(measurement.tobs)]
    if end == None:       
        results = session.query(*sel).\
                                filter(measurement.date >= start).all()
         
    else:
        results = session.query(*sel).\
                                filter(measurement.date >= start).\
                                filter(measurement.date <= end).all()
    

    session.close()
    
    # As given in the instruction. A list is created.
    temp_stats = list(np.ravel(results))

    # However, for readability, it is better to change it to dictionary
    temp_stats_dict = {}
    temp_stats_dict['TMIN'] = temp_stats[0]
    temp_stats_dict['TAVG'] = temp_stats[1]
    temp_stats_dict['TMAX'] = temp_stats[2]

    return jsonify(temp_stats_dict)

if __name__ == '__main__':
    app.run(debug=True)