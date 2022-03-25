g.V().
  has('VertexLabel', '[avm]Design').
  has('[]Name', '__SOURCEDESIGN__').
  in('inside').
  in('inside').
  hasLabel('[]ComponentInstance').
  limit(10).
  project('name', 'id', 'model').
    by('[]Name').
    by('[]ID').
    by(out('component_id').out('component_instance').values('[]Name'))
