g.V().
  has('VertexLabel', '[avm]Design').
  has('[]Name', '__SOURCEDESIGN__').
  in('inside').
  has('VertexLabel', '[]RootContainer').
  project('design', 'objects', 'parameters').
    by('[]Name').
    by(
      __.in('inside').
      has('VertexLabel', '[]ComponentInstance').
      project('name', 'id', 'model', 'assignment').
        by(values('[]Name')).
        by(values('[]ID')).
        by(
          __.out('component_id').
          out('component_instance').
          values('[]Name')).
        by(
          __.in('inside').
          has('VertexLabel', '[]PrimitivePropertyInstance').as('name').
          in('inside').
          in('inside').
          out('value_source').
          out('inside').as('prop').
          group().
            by(select('name').values('[]Name')).
            by(select('prop').values('[]Name'))).
      order().by('name').
      fold()).
    by(
      __.in('inside').
      has('VertexLabel', '[]Property').
      as('prop').
      in('inside').
      in('inside').
      in('inside').
      has('VertexLabel', '[]AssignedValue').
      in('inside').
      in('inside').
      as('val').
      group().
        by(select('prop').values('[]Name')).
        by(select('val').values('value')))