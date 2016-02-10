var gulp = require('gulp'),
	uglify = require('gulp-uglify'),
	concat = require('gulp-concat'),
	csso = require('gulp-csso');

gulp.task('scripts', function(){
	gulp.src('js/*.js')
		.pipe(concat('all.js'))
		.pipe(gulp.dest('static'));
});

gulp.task('styles', function(){
	gulp.src('css/*.css')
		.pipe(concat('styles.css'))
		.pipe(gulp.dest('static'));
});

gulp.task('watch', function(){
	gulp.watch('js/*.js', ['scripts']);
	gulp.watch('css/*.css', ['styles']);
});

gulp.task('default', ['scripts', 'styles', 'watch']);