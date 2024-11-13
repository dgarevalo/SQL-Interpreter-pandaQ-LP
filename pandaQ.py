from antlr4 import *
from pandaQVisitor import pandaQVisitor
from pandaQLexer import pandaQLexer
from pandaQParser import pandaQParser
import streamlit as st
import pandas as pd

# Clases de los visitors
class EvalVisitor(pandaQVisitor):

  # Constructora
  def __init__(self): 
    self.df = None
    self.nombre_tabla = None

    # Creación del diccionario {simbolo, df}
    if 'data_simbols' not in st.session_state:
      st.session_state.data_simbols = {} 

  # Carreguem el dataframe
  def load_table(self):
    self.df = pd.read_csv(self.nombre_tabla + '.csv')


  # Visit a parse tree produced by pandaQParser#root.
  def visitRoot(self, ctx):
    # Caso 1: SIMBOLO
    if ctx.symbol():
      tipo, contenido = self.visit(ctx.symbol())
      return tipo, contenido

    # Caso 2: EXPRESION
    elif ctx.expr():
      return 'tabla', self.visit(ctx.expr())

    # Caso 3: PLOT
    else:
      return 'plot', self.visit(ctx.grafico())


  # Visit a parse tree produced by pandaQParser#symbol.
  def visitSymbol(self, ctx):
    tipo = 'symbol'

    # Caso 1: Borramos el df del simbolo
    if ctx.delete():
      tipo = 'no_mostrar'
      nombre_simbolo = self.visit(ctx.var()).lower()
      if nombre_simbolo in st.session_state.data_simbols:
        del st.session_state.data_simbols[nombre_simbolo]
        st.success('Símbolo eliminado correctamente.')
      else:
        st.error('No se puede borrar un simbolo que no existe.')

    # Caso 2: Mostramos todos los simbolos
    elif ctx.view():
      tipo = 'no_mostrar'
      if len(st.session_state.data_simbols) != 0:
        st.header("Tabla de símbolos")
        i = 1
        for x, df in st.session_state.data_simbols.items():
          st.write(f'{i}) {x}')
          st.write(df)
          i = i + 1
      else:
        st.warning('Aún no se han añadido simbolos a la tabla de símbolos')

    # Caso 3: Guardamos el df del simbolo
    else:
      nombre_simbolo = self.visit(ctx.var()).lower()
      self.df = self.visit(ctx.expr())
      st.session_state.data_simbols[nombre_simbolo] = self.df

    return tipo, self.df


  # Visit a parse tree produced by pandaQParser#grafico.
  def visitGrafico(self, ctx):
    data = self.visit(ctx.var())
    if data in st.session_state.data_simbols:
      # Recuperamos los datos del df para obtener sus cols numéricas
      self.df = st.session_state.data_simbols[data]
      cols_numericas = self.df.select_dtypes(include = 'number').columns

      if cols_numericas.any():
        st.line_chart(self.df[cols_numericas])
      else:
        st.error('No se han indicado columnas numéricas para ser representado.')
    else:
      st.warning('Oops! El símbolo no forma parte de nuestra tabla de símbolos.')

    return self.df


  # Visit a parse tree produced by pandaQParser#expr.
  def visitExpr(self, ctx):
    data = self.visit(ctx.datos()).lower()
    es_simbolo = False

    # Caso 1: es SIMBOLO
    if data in st.session_state.data_simbols:
      self.df = st.session_state.data_simbols[data]
      es_simbolo = True

    # Caso 2: es TABLA
    if not es_simbolo:
      self.nombre_tabla = data
      self.load_table()

    # Extra complements
    if (ctx.innerJoin()):
      self.df = self.visit(ctx.innerJoin())
    
    if (ctx.whereCond()):
      self.df = self.visit(ctx.whereCond())
    
    if (ctx.orderBy()):
      self.df = self.visit(ctx.orderBy())

    # Hay columnas a seleccionar
    columnas_selec = self.visit(ctx.campos())
    if columnas_selec:
      self.df = self.df[columnas_selec]
      
    return self.df


  # Visit a parse tree produced by pandaQParser#campos.
  def visitCampos(self, ctx):
    cols = []
    if ctx.ncols():
      cols = self.visit(ctx.ncols())
    return cols

  # Visit a parse tree produced by pandaQParser#ncols.
  def visitNcols(self, ctx):
    cols = []
    for col in ctx.columna():
      cols.append(self.visit(col))
    return cols

  # Visit a parse tree produced by pandaQParser#columnaSimple.
  def visitColumnaSimple(self, ctx):
    return self.visit(ctx.simple())

  # Visit a parse tree produced by pandaQParser#columnaCalculada.
  def visitColumnaCalculada(self, ctx):
    nueva_columna = self.visit(ctx.modif())
    nuevo_nombre = self.visit(ctx.simple())
    self.df[nuevo_nombre] = nueva_columna
    return nuevo_nombre

  # Visit a parse tree produced by pandaQParser#modif.
  def visitModif(self, ctx):

    # Caso 1: Paréntesis
    if self.visit(ctx.getChild(0)) == '(':
      return self.visit(ctx.getChild(1))

    # Caso 2: Columna o valor
    if ctx.simple():
      return self.visit(ctx.simple())
    elif ctx.NUM():
      return float(ctx.NUM().getText()) 

    # Caso 2: Operación
    if (ctx.modif()):
      izq = self.visit(ctx.modif(0))
      operador = ctx.getChild(1).getText() 
      dre = self.visit(ctx.modif(1))

    # En caso de ser escalares
    if izq not in self.df.columns:
      self.df[izq] = izq
    if dre not in self.df.columns:
      self.df[dre] = dre

    res = 0
    if operador == '+':
      res = self.df[izq] + self.df[dre]
    elif operador == '-':
      res = self.df[izq] - self.df[dre]
    elif operador == '*':
      res = self.df[izq] * self.df[dre]
    elif operador == '/':
      res = self.df[izq] / self.df[dre] if not self.df[dre].eq(0).any() else '+oo'

    return res


  # Visit a parse tree produced by pandaQParser#orderBy.
  def visitOrderBy(self, ctx):
    total_exprs = ctx.orderExpr()
    conds = [self.visitOrderExpr(info) for info in total_exprs]
    columnas = []
    ordenes = []
    for col, asc in conds:
      columnas.append(col)
      ordenes.append(asc)
    # Que se cumplan todas las columnas y ordenes a la vez
    self.df = self.df.sort_values(by = columnas, ascending = ordenes)
    return self.df
    
  # Visit a parse tree produced by pandaQParser#orderExpr. 
  def visitOrderExpr(self, ctx):
    # Columna
    col = self.visit(ctx.simple())
    # Ordenación
    asc = True 
    if ctx.restrict():
      orden = self.visit(ctx.restrict())
      if orden.lower() == 'desc':
        asc = False
    return col, asc


  # Visit a parse tree produced by pandaQParser#whereCond.
  def visitWhereCond(self, ctx):
    return self.visit(ctx.whereType())

  # Visit a parse tree produced by pandaQParser#whereSimple.
  def visitWhereSimple(self, ctx):
    total_exprs = ctx.whereExpr()
    conds = [self.visitWhereExpr(info) for info in total_exprs]
    condiciones = []
    for cond, col, op, elem in conds:
      # Positivo
      if cond:
        condiciones.append(f"{col} {op} {elem}")
      # Negación
      else:
        condiciones.append(f"~({col} {op} {elem})")
    # Creamos una condicion juntando todas las condiciones
    cond_final = " & ".join(condiciones)
    self.df = self.df.query(cond_final)
    return self.df

  # Visit a parse tree produced by pandaQParser#whereExpr.
  def visitWhereExpr(self, ctx):
    cond = True
    if ctx.neg():
      cond = False

    col = self.visit(ctx.simple())
    op = self.visit(ctx.oper())
    if op == '=':
      op = '=='
    elem = self.visit(ctx.comparador())
    return cond, col, op, elem

  # Visit a parse tree produced by pandaQParser#subquery.
  def visitSubquery(self, ctx):
    aux = self.df
    col = self.visit(ctx.simple())
    df = self.visit(ctx.expr())
    # Actualización de la subquery
    self.df = aux[aux[col].isin(df[col])]
    return self.df


  # Visit a parse tree produced by pandaQParser#innerJoin.
  def visitInnerJoin(self, ctx):
    total_exprs = ctx.innerExpr()
    conds = [self.visitInnerExpr(info) for info in total_exprs]
    # Juntamos todas las columnas por tablas
    for nombre, c1, c2 in conds:
      df = pd.read_csv(nombre + '.csv')
      self.df = pd.merge(self.df, df, left_on = c1, right_on = c2, how = 'inner')
    return self.df

  # Visit a parse tree produced by pandaQParser#innerExpr.
  def visitInnerExpr(self, ctx):
    nombre_tabla2 = self.visit(ctx.tabla())
    c1 = self.visit(ctx.simple(0))
    c2 = self.visit(ctx.simple(1))
    return nombre_tabla2, c1, c2


  # Visit a parse tree produced by pandaQParser#comparador.
  def visitComparador(self, ctx):
    if ctx.simple():
      return self.visit(ctx.simple())
    elif ctx.LETRA():
      return ctx.LETRA().getText()
    else:
      return ctx.NUM().getText()

  # Visit a parse tree produced by pandaQParser#simple.
  def visitSimple(self, ctx):
    return ctx.LETRA().getText()

  # Visit a parse tree produced by pandaQParser#datos.
  def visitDatos(self, ctx):
    return ctx.LETRA().getText()

  # Visit a parse tree produced by pandaQParser#tabla.
  def visitTabla(self, ctx):
    return ctx.LETRA().getText()
  
  # Visit a parse tree produced by pandaQParser#restrict.
  def visitRestrict(self, ctx):
    return ctx.getText()

  # Visit a parse tree produced by pandaQParser#oper.
  def visitOper(self, ctx):
    return ctx.getText()
  
  # Visit a parse tree produced by pandaQParser#var.
  def visitVar(self, ctx):
    return ctx.LETRA().getText()

  # Visit a parse tree produced by pandaQParser#delete.
  def visitDelete(self, ctx):
    return ctx.getText()

  # Visit a parse tree produced by pandaQParser#view.
  def visitView(self, ctx):
    return ctx.getText()
  
  # Visit a parse tree produced by pandaQParser#symbols.
  def visitSymbols(self, ctx):
    return ctx.getText()

  # Visit a parse tree produced by pandaQParser#tables.
  def visitTables(self, ctx):
    return ctx.getText()


# Configuración de la cabecera de la página
st.set_page_config(page_title = 'Garcia Arevalo, David')

# Título de la página
st.title('Bienvenid@ a PandaQ!')
st.markdown('El intérprete de SQL que utiliza la librería pandas internamente.')
st.write()

# Obtenemos texto desde cuadro de texto
texto_user = st.text_input('Qué comando quieres ejecutar?')
if st.button('Submit'):
  input_stream = InputStream(texto_user)
  lexer = pandaQLexer(input_stream)
  token_stream = CommonTokenStream(lexer)
  parser = pandaQParser(token_stream)
  tree = parser.root()

  if parser.getNumberOfSyntaxErrors() == 0:
    visitor = EvalVisitor()
    opcion, df = visitor.visit(tree)
    if opcion != 'plot' and opcion != 'no_mostrar':
      st.dataframe(df)

  else:
    print(parser.getNumberOfSyntaxErrors(), 'errors de sintaxi.')
    st.write(parser.getNumberOfSyntaxErrors(), 'errors de sintaxi.')
    print(tree.toStringTree(recog=parser))
    st.write(tree.toStringTree(recog=parser))

st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')
st.write('**********')
st.header("Manual de usuario")
st.write("1. Para seleccionar todos los campos de una tabla:")
st.code("select * from countries;")
st.write('')
st.write("2a. Para seleccionar determinados campos:")
st.code("select first_name, last_name from employees;")
st.write('')
st.write("2b. Para seleccionar campos calculados:")
st.code("select first_name, salary, salary*1.05 as new_salary from employees;")
st.write('')
st.write("3. Para ordenar según nuestro criterio:")
st.code("select * from countries order by region_id, country_name desc;")
st.write('')
st.write("4. Para filtrar según nuestro criterio:")
st.code("select * from countries where not region_id = 1 and not region_id = 3;")
st.write('')
st.write("5. Para hacer un subconjunto de los datos:")
st.write('**Ejemplo 1:**')
st.code("select first_name, department_name from employees \ninner join departments on \n\tdepartment_id = department_id;")
st.write('**Ejemplo 2:**')
st.code("select first_name, last_name, job_title, department_name \nfrom employees inner join departments on department_id = department_id\ninner join jobs on job_id = job_id;")
st.write('')
st.write("6a. Para añadir un nuevo simbolo a la tabla de símbolos:")
st.write('**Ejemplo 1:**')
st.code("q := select first_name, last_name, job_title, department_name \nfrom employees inner join departments on department_id = department_id\ninner join jobs on job_id = job_id;")
st.write('**Ejemplo 2:**')
st.code("d := select first_name, last_name, salary, salary*1.05 as ns \nfrom employees where department_id = 5;")
st.write('')
st.write("6b. Para eliminar un simbolo existente de la tabla de símbolos:")
st.code("delete q;")
st.write('')
st.write("6c. Para visualizar la tabla de símbolos al completo:")
st.code("view all;")
st.write('')
st.write("7. Para visualizar un gráfico por pantalla:")
st.code("plot d;")
st.write('')
st.write("8. Para realizar una subconsulta:")
st.code("select employee_id, first_name, last_name from employees\nwhere department_id in\n(select department_id from departments where location_id = 1700)\norder by first_name, last_name;")
st.write('')
st.write('')
st.write('**********')
st.write('**David García Arévalo**')
st.write('Llenguatges de Programació (2023-2024 Q1)')
st.write('Universitat Politècnica de Catalunya, FIB.')