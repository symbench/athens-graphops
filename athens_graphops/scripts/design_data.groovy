g.V().
  has('VertexLabel', '[avm]Design').
  has('[]Name', '__SOURCEDESIGN__').
  in('inside').
  has('VertexLabel', '[]RootContainer').
  project('design', 'instances', 'parameters', 'connections').
    by('[]Name').
    by(
      __.in('inside').
      has('VertexLabel', '[]ComponentInstance').
      project('name', 'model', 'assignment').
        by(values('[]Name')).
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
      has('VertexLabel', '[]Property').as('prop').
      in('inside').
      in('inside').
      in('inside').
      has('VertexLabel', '[]AssignedValue').
      in('inside').
      in('inside').as('val').
      group().
        by(select('prop').values('[]Name')).
        by(select('val').values('value'))).
    by(
      __.in('inside').
      has('VertexLabel', '[]ComponentInstance').as('instance1').
      in('inside').
      has('VertexLabel', '[]ConnectorInstance').as('connector1').
      out('connector_composition').as('connector2').
      out('inside').as('instance2').
      select('instance1', 'connector1', 'connector2', 'instance2').
        by('[]Name').
      order().by('instance1').by('instance2').
      fold())