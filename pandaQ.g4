// Gramàtica per expressions en SQL
grammar pandaQ;

// Regla principal
root : expr ';'
     | symbol ';'
     | grafico ';'
     ;

// Tablas de simbolos
symbol : var ':=' expr
       | delete var
       | view all
       ;

// Plot por pantalla
grafico : plot var;

// Query del select
expr : select campos from datos (innerJoin)? (whereCond)? (orderBy)?;

// Campos seleccionados
campos : '*' | ncols;
ncols : columna ( ',' columna)*;

columna : simple                        #columnaSimple
        | modif as simple               #columnaCalculada
        ;
        
modif: '(' modif ')'                    
     | modif '*' modif                  
     | modif '/' modif                  
     | modif '-' modif                  
     | modif '+' modif                  
     | simple                           
     | NUM                              
     ;  

// Order by
orderBy: order by orderExpr (',' orderExpr)* ;
orderExpr: simple restrict?;

// Where
whereCond: where whereType;
whereType: whereExpr (and whereExpr)*                   #whereSimple
         | simple in '(' expr ')'                       #subquery
         ;
whereExpr : (neg)? simple oper comparador;

// Inner join
innerJoin: inner join innerExpr (inner join innerExpr)*;
innerExpr: tabla on simple '=' simple;


// Otras definiciones
select: 'select' | 'SELECT';
from: 'from' | 'FROM';
as: 'as' | 'AS';
order: 'order' | 'ORDER';
by: 'by' | 'BY';
where: 'where' | 'WHERE';
restrict: 'asc' | 'ASC' | 'desc' | 'DESC';
and: 'and' | 'AND';
neg: 'not' | 'NOT';
oper: '=' | '<';
comparador: simple | NUM | LETRA;
inner: 'inner' | 'INNER';
join: 'join' | 'JOIN';
on: 'on' | 'ON';
plot: 'plot' | 'PLOT';
in: 'in' | 'IN';
delete: 'delete' | 'DELETE';
view: 'view' | 'VIEW';
all: 'all' | 'ALL';
var: LETRA;
datos: LETRA;
simple: LETRA;
tabla: LETRA;

// Expresiones regulares
LETRA : [a-zA-Z_]+;
NUM : [0-9]+ ('.' [0-9]+)?;

// Ignorar saltos de línea, espacios y tabs
WS  : [ \t\n\r]+ -> skip ;


