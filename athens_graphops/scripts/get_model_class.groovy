g.V().
  has('VertexLabel', '[]Classifications').as('class').
  out('inside').
  has('VertexLabel', '[avm]Component').
  has('[]Name', '__MODELNAME__').
  select('class').
  in('inside').
  values('value')
