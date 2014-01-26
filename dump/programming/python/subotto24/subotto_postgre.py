#! /usr/bin/env python2.7

import sys
import psycopg2
import datetime

if __name__ == "__main__":
    
    conn = psycopg2.connect( database = 'subotto', user = 'subotto', host = 'roma.uz.sns.it', port = 5432, password = 'iPh6Ool7ee', sslmode = 'require') 
    cur = conn.cursor()

    cur.execute("""
SELECT * FROM eventi;
""")
    for resp in cur.fetchall():
        print resp
    

    

    conn.close()
