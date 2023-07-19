
## 2.2. Date and Time Datatype

[https://www.sqlite.org/datatype3.html](https://www.sqlite.org/datatype3.html
)

SQLite does not have a storage class set aside for storing dates and/or times. 
The conventional way to store dates is as a string in a TEXT field. 
These fields can be compared directly (as strings) to determine equality or order. 

For other date-as-string formats, see **Date Strings** on the [Date And Time Functions](https://www.sqlite.org/lang_datefunc.html) page. 

For further manipulations on dates and times, the built-in Date And Time Functions of SQLite convert dates and times between TEXT, REAL, or INTEGER values:

  * TEXT as strings ("YYYY-MM-DD HH:MM:SS.SSS" - with leading zero where required, and four-digit year.)
  
  * REAL as Julian day numbers, the number of days (with fractional part) since noon in Greenwich on November 24, 4714 B.C. 
    according to the proleptic Gregorian calendar.
  * INTEGER as Unix Time, the number of seconds since 1970-01-01 00:00:00 UTC.
    
Applications can chose to store dates and times in any of these formats and freely convert between formats using the [built-in date and time functions.](https://www.sqlite.org/lang_datefunc.html)

---------------------------


# Date And Time Functions

[https://www.sqlite.org/lang_datefunc.html](https://www.sqlite.org/lang_datefunc.html)

The conventional way to store dates is as a string in a TEXT field. 
These fields can be compared directly (as strings) to determine equality or order.

To convert to other date representations, SQLite supports five date and time functions. All take a *timestring* (a subset of IS0 8601 date and time formats, listed below) as an argument. The timestring is followed by zero or more modifiers. The strftime() function also takes a format string as its first argument.

  1. **date(**timestring, modifier, modifier, ...**)** *Returns the date as a string: "YYYY-MM-DD".*
  2. **time(**timestring, modifier, modifier, ...**)** *Returns the time as a string: "HH:MM:SS".*
  3. **datetime(**timestring, modifier, modifier, ...**)** *Returns a string: "YYYY-MM-DD HH:MM:SS".*
  4. **julianday(**timestring, modifier, modifier, ...**)** *Returns the Julian day as an REAL - the number of days (and fractional part) since noon in Greenwich on November 24, 4714 B.C. (Proleptic Gregorian calendar).*
  5. **strftime(**format, timestring, modifier, modifier, ...**)** *Returns the date formatted according to the format string specified as the first argument. The format string supports the most common substitutions found in the strftime() function from the standard C library plus two new substitutions, %f and %J.*
  
The following is a complete list of valid strftime() substitutions: 
   
... and later...

## Time Strings

SQLite accepts time strings in any of the following formats.
Include leading zero's where necessary, and use four-digit years.

1. YYYY-MM-DD
2. YYYY-MM-DD HH:MM
3. YYYY-MM-DD HH:MM:SS
1. YYYY-MM-DD HH:MM:SS.SSS
1. YYYY-MM-DDTHH:MM
1. YYYY-MM-DDTHH:MM:SS
1. YYYY-MM-DDTHH:MM:SS.SSS
1. HH:MM
1. HH:MM:SS
1. HH:MM:SS.SSS
1. now
1. DDDDDDDDDD 

... and later...

## Examples

Examples

Compute the current date. *Returns timestring.*

    SELECT date('now');  -- Result: 2018-03-07

Compute the last day of the current month. *Returns timestring.*

    SELECT date('now','start of month','+1 month','-1 day'); -- Result: 2018-03-31

Compute the date and time given a unix timestamp 1092941466. *Returns timestring.*

    SELECT datetime(1092941466, 'unixepoch'); -- Result: 2004-08-19 18:51:06

Compute the date and time given a unix timestamp 1092941466, and compensate for your local timezone. *Returns timestring.*

    SELECT datetime(1092941466, 'unixepoch', 'localtime'); -- Result: 2004-08-19 14:51:06

Compute the current unix timestamp. *Returns INTEGER.*

    SELECT strftime('%s','now');  -- Result: 1520444198

Compute the number of days since the signing of the US Declaration of Independence.  *Returns REAL - days and fractions of a day.*

    SELECT julianday('now') - julianday('1776-07-04'); -- Result: 88269.7339379285

Compute the number of seconds since a particular moment in 2004:  *Returns INTEGER.*

    SELECT strftime('%s','now') - strftime('%s','2004-01-01 02:34:56'); -- Result: 447519729

Compute the date of the first Tuesday in October for the current year. *Returns timestring.*

    SELECT date('now','start of year','+9 months','weekday 2'); -- Result: 2018-10-02

Compute the time since the unix epoch in seconds (like strftime('%s','now') except includes fractional part). *Returns REAL - days and fractions of a day.*

    SELECT (julianday('now') - 2440587.5)*86400.0; -- Result: 1520444280.01899
