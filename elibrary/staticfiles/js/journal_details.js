//function test(a) {
//    var value = a.value;
//    document.getElementById('text-search1').innerHTML = "Вывод статей за " + value + " год";
//    if (value === '2019') {
//        var array = ["1", "3", "5", "7"];
//    }
//    else if (value === '2018') {
//        var array = ["2", "4", "6", "8"];
//    }
//    else {
//        var array = [];
//    }
//    var string = "";
//    for (i = 0; i < array.length; i++) {
//        string = string + "<option>" + array[i] + "</option>";
//    }
//    string = "<select name='select'>" + string + "</select>";
//    document.getElementById('text-search').innerHTML = string;
//
//}
//alert(lang)
//alert(journal_id)


//$(document).ready(function(){
//
//}

/*function test(a) {
    var value = a.value;  
    document.getElementById('text-search1').innerHTML = "Вывод статей за " + value + " год";
    if (value === '2019') {
        var array = ["1", "3", "5", "7"];
    }
    else if (value === '2018') {
        var array = ["2", "4", "6", "8"];
    }
    else {
        var array = [];
    }
    var string = "";
    for (i = 0; i < array.length; i++) {
        string = string + "<option>" + array[i] + "</option>";
    }
    string = "<select name='select'>" + string + "</select>";
    document.getElementById('text-search').innerHTML = string;
}*/


$(document).ready(function(){

});

function change_year(selected_year) {
    $.ajax({
        url: '/issue_by_year',
        type: 'get',
        data: {
            journal_id: journal_id,
            year: selected_year.value
        },
        success: function(response){

            var volume_array = response.volumes;
            var num_array = response.numbers

            var volume_string = "";
            var num_string = "";
            for (i = 0; i < volume_array.length; i++) {
                volume_string = volume_string + "<option value='"+ volume_array[i] + "'>" +volume_array[i] + "</option>";
            }
            for (j = 0; j < num_array.length; j++) {
                num_string = num_string + "<option value='"+ num_array[j] +"'>" + num_array[j] + "</option>";
            }
            document.getElementById('volume_select').innerHTML = volume_string;
            document.getElementById('number_select').innerHTML = num_string;

            render_articles(response.articles)
        }
    });
}

function change_volume(selected_volume){
    $.ajax({
        url: '/issue_by_volume',
        type: 'get',
        data: {
            journal_id: journal_id,
            year: $('#year_select').children("option:selected").val(),
            volume: selected_volume.value,
        },
        success: function(response){
            
            var num_array = response.numbers

            var num_string = "";

            for (j = 0; j < num_array.length; j++) {
                num_string = num_string + "<option value='"+ num_array[j] + "'>" + num_array[j] + "</option>";
            }
            document.getElementById('number_select').innerHTML = num_string;

            render_articles(response.articles)

        }
    });
}

function change_number(selected_number){
    $.ajax({
        url: '/issue_by_number',
        type: 'get',
        data: {
            journal_id: journal_id,
            year: $('#year_select').children("option:selected").val(),
            volume: $('#volume_select').children("option:selected").val(),
            number: selected_number.value,
        },
        success: function(response){
            render_articles(response.articles)
        }
    });
}



// <div class="search-event specific-event">
//     <h3><a href="{{a.pdf.url}}">
//         {% default_translate a.rus_title a.eng_title a.eng_title a.rus_title %}
//     </a></h3>
//     <p><b>{% translate 'Аннотация' 'Annotation' %}:</b></p>
//     <p>
//         {% default_translate a.rus_annotation a.eng_annotation a.eng_annotation a.rus_annotation ""%}
//     </p>
//     <p><b>{% translate 'Авторы' 'Authors' %}: </b>
//         {% for author in a.authors.all %}
//             {% default_translate author.rus_surname author.eng_surname author.eng_surname author.rus_surname ""%}
//              {% default_translate author.rus_initials author.eng_initials author.eng_initials author.rus_initials ""%},
//         {% endfor %}
//     </p>
//     <p><b>{% translate 'Ключевые слова' 'Keywords' %}: </b>
//         {% for k in a.keywords.all %}
//             {{k}},
//         {% endfor%}
//     </p>
//     <p><b>{% translate 'Скачать файл' 'Download' %}: </b><a href="{{a.pdf.url}}"><i class="fa fa-file-pdf-o" aria-hidden="true"></i></a></p>
//     <p><b>Elibrary: </b><a href="{{ article.furl }}">{{ a.furl}}</a></p>
// </div>


//def default_translate(context, rus_version, eng_version, rus_default="", eng_default="", total_fail_default=""):
//    if context["lang"] == "ENG":
//        if eng_version is None:
//            return total_fail_default if eng_default is None else eng_default
//        else:
//            return eng_version
//    else:
//        if rus_version is None:
//            return total_fail_default if rus_default is None else rus_default
//        else:
//            return rus_version

// def translate(context, rus_version, eng_version):
//     return eng_version if context["lang"] == "ENG" else rus_version


function render_articles(articles){
    var mega_string = "";
    for (i = 0; i < articles.length; i++) {
        var article = articles[i];
        var article_string = "<div id='option_result' class='search-event specific-event'> <h3>\
                <a target='_blank' href='"+ article.pdf_url+"'>" + default_translate(lang, article.rus_title, article.eng_title, article.eng_title, article.rus_title, "") +"</a></h3><p><b>"+ translate(lang, "Аннотация", "Annotation") +":</b></p>\
                <p>"+ default_translate(lang, article.rus_annotation, article.eng_annotation, "", "", "") + "</p>"

        var article_authors = "<p><b>" + translate(lang, "Авторы", "Authors") + ": </b>"
        for(k = 0; k < article.authors.length; k++) {
            article_authors += default_translate(lang, article.authors[k].rus_surname, article.authors[k].eng_surname, "", "", "") + " " + default_translate(lang, article.authors[k].rus_initials, article.authors[k].eng_initials, "", "", "")
            if (k < article.authors.length - 1){ article_authors += ", " }
        }
        article_authors += "</p>"
        article_string += article_authors

        article_keywords = "<p><b>"+ translate(lang, "Ключевые слова", "Keywords")+": </b>"
        for(k = 0; k < article.keywords.length; k++) {
            article_keywords += default_translate(article.keywords[k].lang, article.keywords[k].word, article.keywords[k].word, "", "", "")
            if (k < article.keywords.length - 1){ article_keywords += ", " }
        }
        article_keywords += "</p>"
        article_string += article_keywords

        article_string += "<p><b>"+ translate(lang, "Скачать", "Download") + ": </b>" +"<a target='_blank' href='"+ article.pdf_url + "'><i class='fa fa-file-pdf-o' aria-hidden='true'></i></a></p><p><b>Elibrary: </b>\
        <a href='"+ article.furl+"'>"+ default_translate(article.furl, article.furl, "", "") + "</a></p></div>"

        if (article_string === undefined) { article_string = '' }
        mega_string += article_string;
    }
    document.getElementById('event-details').innerHTML = mega_string
}


function translate(lang, rus_version, eng_version) {
    if (lang === "ENG") {
        return eng_version
    }
    else {
        return rus_version
    }
}

function default_translate(lang, rus_version, eng_version, rus_default=" ", eng_default=" ", total_fail_default=""){
    if (lang === "ENG") {
        if (eng_version === null) {
            if (eng_default === null) {
                return total_fail_default
            }
            else {
                return eng_default
            }
        }
        else {
            return eng_version
        }
    }
    else {
        if (rus_version === null) {
            if (rus_default === null) {
                return total_fail_default
            }
            else {
                return rus_default
            }
        }
        else {
            return rus_version
        }
    }
}