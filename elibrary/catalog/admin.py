from django.contrib import admin
from catalog.models import *

class RubricListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Rubric'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'rubric'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('chm', 'Chemistry'),
            ('blg', 'Biology'),
            ('phl', 'Physiology'),
        )


    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.

        def grouped_by_rubric(self, rubric_name):
            for j in self.all():
                if j.rubrics.filter(name=rubric_name).exists():
                    yield j

        if self.value() == 'chm':
            return queryset.filter(rubrics__name="chm")
        if self.value() == 'blg':
            return queryset.filter(rubrics__name="blg")
        if self.value() == 'phl':
            return queryset.filter(rubrics__name="phl")


import nested_admin

class AuthorInline(nested_admin.NestedTabularInline):
    model = Author

class ReferenceInline(nested_admin.NestedTabularInline):
    model = Reference

class ArticleInline(nested_admin.NestedStackedInline):
    model = Article
    inlines = [AuthorInline, ReferenceInline]

class IssueInline(admin.TabularInline):
    model = Issue

class JournalAdmin(admin.ModelAdmin):
    list_filter = (RubricListFilter,)
    inlines = [
        IssueInline,
    ]

class IssueAdmin(nested_admin.NestedModelAdmin):
    inlines = [ArticleInline]

class ScienceEventAdmin(admin.ModelAdmin):
    list_filter = (RubricListFilter,)

class ArticleAdmin(nested_admin.NestedModelAdmin):
    search_fields = ('rus_title', 'eng_title')
    list_filter = (RubricListFilter,)
    inlines = [
        AuthorInline,
    ]

class AuthorAdmin(admin.ModelAdmin):
    search_fields = ('rus_surname', 'eng_surname')

class VideoAdmin(admin.ModelAdmin):
    search_fields = ('rus_title', 'eng_title')


class KeywordAdmin(admin.ModelAdmin):
    search_fields = ('word',)

class ReportAdmin(admin.ModelAdmin):
    search_fields = ('rus_title', 'eng_title')
    inlines = [
        AuthorInline,
    ]


admin.site.register(Journal, JournalAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Publication)
admin.site.register(ScienceEvent)
admin.site.register(Report,ReportAdmin)
admin.site.register(Video, VideoAdmin)
