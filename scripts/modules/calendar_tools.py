def get_season_info(db, season):
    cursor = db.cursor()
    cursor.execute('''
    SELECT startdate, enddate, bdate
    FROM season 
    LEFT JOIN blackout ON season.id=season_id
    WHERE season.id=%s''', season)
    blackouts = []
    for start_date, end_date, bdate in cursor.fetchall():
        blackouts.append(bdate)
    return start_date, end_date, blackouts
