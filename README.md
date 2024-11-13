# LP Practice: SQL Interpreter pandaQ

## Installation & Execution
1) First, after downloading the files from the `.zip`, you need to compile the grammar:
```bash
antlr4 -Dlanguage=Python3 -no-listener -visitor pandaQ.g4 
```

2) Next, run the interpreter program:
```bash
streamlit run pandaQ.py 
```

## Notes
The program's interface is divided into two parts:

* The first part displays a welcome message, followed by a text box for entering queries and a button to execute the commands.

* The second part contains a user manual at the bottom with some code examples that can be pasted into the text box. However, you can also test the interpreter with any commands you like.

## EXTENSIONS
Two extensions have been implemented, in addition to all the practice requirements:

* Delete a symbol from the symbol table:
```streamlit
delete id;
```

* Display the entire symbol table:
```streamlit
view all;
```

These features have been created to improve the usability of the interpreter, allowing users to have more control over the symbols and, therefore, the data processing.
