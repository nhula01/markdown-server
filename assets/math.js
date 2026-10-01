// Typeset the copied source only for display; leave Optimum and the catalog intact.
document.querySelectorAll('.guide-verbatim').forEach((guide) => {
  renderMathInElement(guide, {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false},
      {left: '\\(', right: '\\)', display: false},
      {left: '\\[', right: '\\]', display: true},
      {left: '\\begin{equation}', right: '\\end{equation}', display: true},
      {left: '\\begin{align}', right: '\\end{align}', display: true},
    ],
    throwOnError: false,
    trust: false,
    output: 'htmlAndMathml',
  });
});
