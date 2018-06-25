$(document).ready(function() {
    $('.simple-mde').each(function() {
        var simpleMDE = new SimpleMDE({
            element: this,
            indentWithTabs: false,
            spellChecker: false,  // Disabled because it doesn't understand Russian
            toolbar: [
                'bold',
                'italic',
                '|',
                'heading-smaller',
                'heading-bigger',
                'heading-1',
                'heading-2',
                'heading-3',
                '|',
                'quote',
                'unordered-list',
                'ordered-list',
                '|',
                'link',
                'horizontal-rule',
                '|',
                'code',
                'table',
                '|',
                'fullscreen',
            ],
        });
        simpleMDE.render();
    });
});
