/* Load nathjax if needed */

var luffy = luffy || {};
luffy.mathjax = function() {
    var delim = "·"; // It's "middle dot"
    var mathjax = "//d3eoax9i5htok0.cloudfront.net/mathjax/1.1-latest/MathJax.js";

    /* Don't load if we don't find the delimiter. */
    if ($("#lf-main").text().indexOf(delim) === -1) return;

    /* Otherwise, load. Input: TeX/AMS. Output: HTML+CSS.*/
    yepnope({ load: mathjax + "?config=TeX-AMS_HTML-full&delayStartupUntil=configured",
	      complete: function() {
		  /* Add more configuration stuff */
		  MathJax.Hub.Config({
		      elements: ["lf-main"], // Only process part of the page.
		      tex2jax: {
			  inlineMath: [ [delim,delim] ],
			  displayMath: [ [delim + delim, delim + delim] ],
			  processEnvironments: false
		      },
		      "HTML-CSS": {
			  scale: 97,
			  showMathMenu: false
		      }
		  });
		  MathJax.Hub.Configured();
		  MathJax.Hub.Startup.onload();
	      }});
};
