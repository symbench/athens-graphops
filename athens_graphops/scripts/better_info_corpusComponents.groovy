g.V().
  has('VertexLabel', '[]Classifications').as('class').
  in('inside').as('class_name').
  select('class').
  out('inside').
  has('VertexLabel', '[avm]Component').
  project('Component', 'Classification').
    by('[]Name').
    by(select('class_name').values('value'))
