DATA WORK.TABLE_15000_COLS;
  ARRAY cols[15000] col1-col15000;
  
  /* Initialize all columns with some sample data */
  DO i = 1 TO 15000;
    cols[i] = i;
  END;
  
  /* Create a few sample rows */
  DO row = 1 TO 10;
    DO i = 1 TO 15000;
      cols[i] = row * i;
    END;
    OUTPUT;
  END;
  
  DROP i row;
RUN;
