

call npx.cmd tailwindcss -i input.css -o output.css

del /q blog\templates\
copy calendar.html ..\blog\templates\calendar.html
copy page.html ..\blog\templates\page.html
copy search.html ..\blog\templates\search.html
copy container.html ..\blog\templates\container.html
copy tags.html ..\blog\templates\tags.html
copy output.css ..\blog\templates\output.css