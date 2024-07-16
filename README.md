# What
A tool to scrape the internet for your own posts and save them neatly locally

Then -- to display them on a website

And even then -- to display them as a toycommons-connected tool.

# To Do

1) Model [x]
2) Storage (!) -- todo. let it store and serve filenames (images) so web can use them them; 
it also can connect to toycommons to sync info and stuff.
3) CLI interface
4) Editing, searching and viewing functionality
5) Scrapers (blogs, facebook, two-way TG reader)
6) toycommons two-way sync of images and files
7) web face
8) privacy config
9) xml\tg running scraper.


Tooling should be common in format to support all possibilities. Roughly:

1) bold, italic, strikethrough, headers, URL, inner-URL
2) ignore tables but allow sidenotes
3) quote style
4) code style 
5) inline image, banner image, video, image carousel (?)


Parameters
* header
* body
* visibility
* datetime
* tags
* original URL if possible
* original comments if available --> each being the same.

**body**: embedded YT videos, [MORE] tag and short text processing, hint highlight.
basic formatting, positioning, images, carousels func, URLs

positioning: allow instagram posts to be converted into [image side] | [text side]



```
<div align="right"><b>08.12.2012</b> в 15:44</div>Пишет <a class="TagJIco" href="/member/?499109" title="профиль" target=_blank>&nbsp;</a><a class="TagL" href="http://rik-falkorn.diary.ru" title="дневник: Жизнь молодого лиса" target=_blank>Рик Фалькорн</a>:

 <span class="quote_text"><div class=blockquote><div align="right"><b>08.12.2012</b> в 12:47</div>Пишет <a class="TagJIco" href="/member/?918667" title="профиль" target=_blank>&nbsp;</a><a class="TagL" href="http://through-singularity.diary.ru" title="дневник: Space Opera" target=_blank>.Big Bad Wolf</a>:

 <span class="quote_text"><div class="blockquote"><b>Это ОППАДЖИГУРДАА запало мне в душу :3</b>
<div align="right"><b>08.12.2012</b> в 12:01</div>Пишет <a class="TagJIco" href="/member/?878093" title="профиль" target=_blank>&nbsp;</a><a class="TagL" href="http://Soul-RnD.diary.ru" title="дневник: [... &#12450;&#12452;&#12473;&#12288;&#12513;&#12463;&#65306;&#12521;&#12531;&#12473; ...]&#12288;" target=_blank>Soul_RnD</a>:

 <span class="quote_text"><div class="blockquote"><b>OPPAGHIGURSTYLE!!</b>
Видео сделало мое утро xDDD

<div align="right"><b>08.12.2012</b> в 00:53</div>Пишет <a class="TagJIco" href="/member/?166385" title="профиль" target=_blank>&nbsp;</a><a class="TagL" href="http://ars-rnd.diary.ru" title="дневник: Хроники Черной Луны" target=_blank>Rubeus Blackmoon</a>:

 <span class="quote_text"><div class="blockquote"><b>#ОППАДЖИГУРДА</b>
[MORE=Предыстория]<i>5 декабря. Твиттер.</i>

НИКИТА ДЖИГУРДА(18+) &#8207;@DZHIGURDA12
Если Этот ТВИТ наберёт 12000 ретвитов до 12.12.2012, то Я станцую в килте ГАНГНАМ СТАЙЛ на Красной Площади и выложу видео!!!

<i>Тот же день.</i>

НИКИТА ДЖИГУРДА(18+) &#8207;@DZHIGURDA12
За шесть часов #ОППАДЖИГУРДА набрал необходимые ретвиты - пойду гладить килт...

<i>Вчера.</i>

<img src="http://distilleryimage4.instagram.com/26b6b79c405a11e2aeb222000a1f9e7e_7.jpg">

<s><i>Говорят, вечером будет само видео.</i></s>

<i>А вот что он сам пишет по этому поводу:</i>
НИКИТА ДЖИГУРДА(18+) &#8207;@DZHIGURDA12

#ОППАДЖИГУРДА
любит ВАС - О ДА
и захуЯрит в кИлте
на площади труда
танец ГАНГАМСТАЙЛ
чтоб КОСМОСА ПИЗДА
любила НАС всегда!!!![/MORE]

UPD. А вот и обещанное видео.
<iframe width="640" height="360" src="http://www.youtube.com/embed/B9cQ9gOSEIk" frameborder="0" allowfullscreen></iframe>

P.S.

НИКИТА ДЖИГУРДА(18+) &#8207;@DZHIGURDA12
НЕТ ВРЕМЕНИ ОБЪЯСНЯТЬ! Если этот ТВИТ наберет 21000 ретвитов до 21.12.2012, то Я забацаю клип ГАНГАМСТАЙЛ По-Русски и отменю им Конец Света!

<i>*facepalm*</i>

</div></span><small><a href="http://ars-rnd.diary.ru/p183290184.htm" target=_blank>URL записи</a></small>

</div></span><small><a href="http://Soul-RnD.diary.ru/p183312098.htm" target=_blank>URL записи</a></small>

</div></span><small><a href="http://through-singularity.diary.ru/p183312887.htm" target=_blank>URL записи</a></small>

</div></span><small><a href="http://rik-falkorn.diary.ru/p183316602.htm" target=_blank>URL записи</a></small>
```