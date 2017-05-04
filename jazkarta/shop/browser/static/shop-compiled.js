define("mockup-utils",["jquery"],function(a){"use strict";var b=function(b){var c=this,d={pattern:null,vocabularyUrl:null,searchParam:"SearchableText",pathOperator:"plone.app.querystring.operation.string.path",attributes:["UID","Title","Description","getURL","portal_type"],batchSize:10,baseCriteria:[],sort_on:"is_folderish",sort_order:"reverse",pathDepth:1};return c.options=a.extend({},d,b),c.pattern=c.options.pattern,void 0!==c.pattern&&null!==c.pattern||(c.pattern={browsing:!1,basePath:"/"}),c.options.url&&!c.options.vocabularyUrl?c.options.vocabularyUrl=c.options.url:c.pattern.vocabularyUrl&&(c.options.vocabularyUrl=c.pattern.vocabularyUrl),c.valid=Boolean(c.options.vocabularyUrl),c.getBatch=function(a){return{page:a?a:1,size:c.options.batchSize}},c.getCurrentPath=function(){var a,b=c.pattern;a=c.currentPath?c.currentPath:b.currentPath,"function"==typeof a&&(a=a());var d=a;return d||(d=b.basePath?b.basePath:b.options.basePath?b.options.basePath:"/"),d},c.getCriterias=function(b,d){void 0===d&&(d={}),d=a.extend({},{useBaseCriteria:!0,additionalCriterias:[]},d);var e=[];return d.useBaseCriteria&&(e=c.options.baseCriteria.slice(0)),b&&(b+="*",e.push({i:c.options.searchParam,o:"plone.app.querystring.operation.string.contains",v:b})),d.searchPath?e.push({i:"path",o:c.options.pathOperator,v:d.searchPath+"::"+c.options.pathDepth}):c.pattern.browsing&&e.push({i:"path",o:c.options.pathOperator,v:c.getCurrentPath()+"::"+c.options.pathDepth}),e=e.concat(d.additionalCriterias)},c.getQueryData=function(a,b){var d={query:JSON.stringify({criteria:c.getCriterias(a),sort_on:c.options.sort_on,sort_order:c.options.sort_order}),attributes:JSON.stringify(c.options.attributes)};return b&&(d.batch=JSON.stringify(c.getBatch(b))),d},c.getUrl=function(){var b=c.options.vocabularyUrl;return b+=b.indexOf("?")===-1?"?":"&",b+a.param(c.getQueryData())},c.selectAjax=function(){return{url:c.options.vocabularyUrl,dataType:"JSON",quietMillis:100,data:function(a,b){return c.getQueryData(a,b)},results:function(a,b){var c=10*b<a.total;return{results:a.results,more:c}}}},c.search=function(b,d,e,f,g,h){void 0===g&&(g=!0),void 0===h&&(h="GET");var i=[];g&&(i=c.options.baseCriteria.slice(0)),i.push({i:b,o:d,v:e});var j={query:JSON.stringify({criteria:i}),attributes:JSON.stringify(c.options.attributes)};a.ajax({url:c.options.vocabularyUrl,dataType:"JSON",data:j,type:h,success:f})},c},c=function(b){var c=this;c.className="plone-loader";var d={backdrop:null,zIndex:10005};return b||(b={}),c.options=a.extend({},d,b),c.init=function(){c.$el=a("."+c.className),0===c.$el.length&&(c.$el=a("<div><div></div></div>"),c.$el.addClass(c.className).hide().appendTo("body"))},c.show=function(b){c.init(),c.$el.show();var d=c.options.zIndex;"function"==typeof d?d=Math.max(d(),10005):(d=10005,a(".plone-modal-wrapper,.plone-modal-backdrop").each(function(){d=Math.max(d,a(this).css("zIndex")||10005)}),d+=1),c.$el.css("zIndex",d),void 0===b&&(b=!0),c.options.backdrop&&(c.options.backdrop.closeOnClick=b,c.options.backdrop.closeOnEsc=b,c.options.backdrop.init(),c.options.backdrop.show())},c.hide=function(){c.init(),c.$el.hide()},c},d=function(){var b=a('input[name="_authenticator"]');return 0===b.length?(b=a('a[href*="_authenticator"]'),b.length>0?b.attr("href").split("_authenticator=")[1]:""):b.val()},e=function(a){return void 0===a&&(a="id"),a+Math.floor(65536*(1+Math.random())).toString(16).substring(1)},f=function(a,b){void 0===b&&(b="id");var c=a.attr("id");return c=void 0===c?e(b):c.replace(/\./g,"-"),a.attr("id",c),c},g=function(){var a=window;return a.parent!==window&&(a=a.parent),a},h=function(b){return a(/<body[^>]*>((.|[\n\r])*)<\/body>/im.exec(b)[0].replace("<body","<div").replace("</body>","</div>")).eq(0).html()},i={dragAndDrop:function(){return"draggable"in document.createElement("span")},fileApi:function(){return"undefined"!=typeof FileReader},history:function(){return!(!window.history||!window.history.pushState)}},j=function(b){return"string"==typeof b&&(b=a.trim(b).toLowerCase()),["false",!1,"0",0,"",void 0,null].indexOf(b)===-1},k=function(b){return a("<div/>").text(b).html()},l=function(a){return a.replace(/<[^>]+>/gi,"")};return{bool:j,escapeHTML:k,removeHTML:l,featureSupport:i,generateId:e,getAuthenticator:d,getWindow:g,Loading:c,loading:new c,parseBodyTag:h,QueryHelper:b,setId:f}}),require(["jquery","mockup-utils"],function(a,b){if(a("body").hasClass("template-review-cart"))a(".jaz-shop-cart-wrapper").hide();else{a(".jaz-shop-cart-wrapper").show();var c=a("body").attr("data-portal-url");a(document).on("click",".jaz-shop-add",function(d){d.preventDefault();var e=a(this).attr("data-uid");a.post(c+"/shopping-cart",{add:e,_authenticator:b.getAuthenticator()},function(b){a(".jaz-shop-cart-wrapper").replaceWith(b)},"html")})}}),define("/home/witek/dev/mex_sprint/zinstance/src/jazkarta.shop/jazkarta/shop/browser/static/shop.js",function(){});
//# sourceMappingURL=shop-compiled.js.map