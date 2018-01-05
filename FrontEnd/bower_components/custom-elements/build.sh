function compile () {
	# Give names to arguments
	input=$1
	output=$2

	# Read the js file
	js=$(<$input)

	# Google Closure Compiler API
	url="http://closure-compiler.appspot.com/compile"
	# WHITESPACE_ONLY, SIMPLE_OPTIMIZATIONS, ADVANCED_OPTIMIZATIONS
	level="SIMPLE_OPTIMIZATIONS"
	# text, json, xml
	format="text"
	# compiled_code, warnings, errors, statistics
	info="compiled_code"
	# compile using remote API
	code=$(curl --data-urlencode "js_code=$js" --data "compilation_level=$level&output_format=$format&output_info=$info" $url)
	# Write out
	echo "$code" > $output
}

rm -rf ./dist/*
echo "Optomising using Google Closure"
compile "./src/CustomElements.js" "./dist/CustomElements.min.js"
compile "./src/MutationObserver.js" "./dist/MutationObserver.min.js"
