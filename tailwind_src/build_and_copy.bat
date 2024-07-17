

call npx.cmd tailwindcss -i input.css -o output.css

del /q blog_web\templates\
copy calendar.html ..\blog_web\templates\calendar.html
copy page.html ..\blog_web\templates\page.html
copy search.html ..\blog_web\templates\search.html
copy container.html ..\blog_web\templates\container.html
copy tags.html ..\blog_web\templates\tags.html
copy output.css ..\blog_web\templates\output.css