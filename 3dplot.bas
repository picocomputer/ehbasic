' 3D Plot
' A program by Mark Bramhall publisherd in BASIC Computer Games
' https://www.atariarchives.org/basicgames/showpage.php?page=167
'
' Some functions to try:
' 5 DEF FNA(Z)=30*EXP(-Z*Z/100)
' 5 DEF FNA(Z)=SQR(900.01-Z*Z)*.9-2
' 5 DEF FNA(Z)=30*(COS(Z/16)  2   <-- My physical copy has this typo too
' 5 DEF FNA(Z)=30-30*SIN(Z/18)
' 5 DEF FNA(Z)=30*EXP(-COS(Z/16))-30
' 5 DEF FNA(Z)=30*SIN(Z/10)

5 DEF FNA(Z)=30*EXP(-Z*Z/100)
100 PRINT
110 FOR X=-30 TO 30 STEP 1.5
120 L=0
130 Y1=5*INT(SQR(900-X*X)/5)
140 FOR Y=Y1 TO -Y1 STEP -5
150 Z=INT(25+FNA(SQR(X*X+Y*Y))-.7*Y)
160 IF Z<=L THEN 190
170 L=Z
180 PRINT TAB(Z)"*";
190 NEXT Y
200 PRINT
210 NEXT X
300 END
