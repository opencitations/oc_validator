document.addEventListener('click', function(event) {
    const element = event.target;
    const onclickAttr = element.getAttribute('onclick');

    if (!onclickAttr || !onclickAttr.includes('highlightInvolvedElements(this)')) {
        document.querySelectorAll('.highlight').forEach(el => {
            el.classList.remove('highlight');
        });
    }
});

function highlightInvolvedElements(element) {
    const classList = element.className.split(' ');
    const targetClass = classList.find(className => className.startsWith('err-idx-'));
    if (targetClass) {
        document.querySelectorAll('.highlight').forEach(el => {
            el.classList.remove('highlight');
        });
        const elements = document.querySelectorAll('.' + targetClass);
        elements.forEach(el => {
            el.classList.add('highlight');
        });
    }
}
