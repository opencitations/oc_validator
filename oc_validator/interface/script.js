    document.addEventListener('click', function(event) {
        const element = event.target;
        const onclickAttr = element.getAttribute('onclick');

        if (!onclickAttr || !onclickAttr.includes('highlightInvolvedElements(this)')) {
            // Remove all highlights globally across all tables
            document.querySelectorAll('.highlight').forEach(el => {
                el.classList.remove('highlight');
            });
        }
    });

    function highlightInvolvedElements(element) {
        const classList = element.className.split(' ');
        const targetClass = classList.find(className => className.startsWith('err-idx-'));
        if (targetClass) {
            // Clear highlights across all tables
            document.querySelectorAll('.highlight').forEach(el => {
                el.classList.remove('highlight');
            });

            // Add highlights only within the same table as the clicked element
            const parentTable = element.closest('table');
            if (parentTable) {
                const elements = parentTable.querySelectorAll('.' + targetClass);
                elements.forEach(el => {
                    el.classList.add('highlight');
                });
            }
        }
    }
