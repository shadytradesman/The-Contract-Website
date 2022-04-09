/* global window */
import 'htmx.org';
window.jQuery = window.$ = require('jquery');

const $ = window.$;

require('htmx.org')
require('bootstrap');
require('eonasdan-bootstrap-datetimepicker');

var moment = require('moment');
moment().format();

$(() => {
});
