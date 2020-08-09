# WaveFunctionCollapse
Procedural generation with constraints based on Wave Function Collapse algorithm.

## 1D
For an input string generates string of similar structure, respecting all constrains in an input string.

	INPUT: "AAXBBX", N=2, cellnum=8:
	OUTPUT: "XAAAXBXBXBBBXAAA"

	INPUT: "DOG", N=3, cellnum=5
	OUTPUT: "OGDOGDOGDOGDOGD"

## 2D
For an input:

<img src="WaveFunctionCollapse/2D/example_input.png">

here is an output:

<img src="WaveFunctionCollapse/2D/example.gif">

### Remember:<br>
- Not all inputs are viable<br>
- Input should be small and simple<br>
- Big input will add a lot of constraints and it may take ages to complete<br>
- Often it does have a "deadlock" meaning it is unsolvable, script will end without an output<br>


