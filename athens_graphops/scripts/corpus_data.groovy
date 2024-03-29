g.V().
  has('VertexLabel', '[]Classifications').as('class').
  in('inside').as('class_name').
  select('class').
  out('inside').
  has('VertexLabel', '[avm]Component').as('comp').
  project(
    'class',
    'model',
    'id',
    "schema_version",
    'properties',
    'parameters',
    'connectors').
    by(select('class_name').values('value')).
    by('[]Name').
    by('[]ID').
    by('[]SchemaVersion').
    by(
      __.in('inside').
      has('VertexLabel', '[]Property').as('prop').
      in('inside').
      in('inside').
      has(
        '[http://www.w3.org/2001/XMLSchema-instance]type',
        '[avm]FixedValue').
      in('inside').
      in('inside').
      group().by(select('prop').values('[]Name')).by(values('value'))).
    by(
      __.in('inside').
      has('VertexLabel', '[]Property').as('prop').
      in('inside').
      in('inside').
      has(
        '[http://www.w3.org/2001/XMLSchema-instance]type',
        '[avm]ParametricValue').
        as('val').
      group().
        by(select('prop').values('[]Name')).
        by(
          union(
            select('val').
            in('inside').
            has('VertexLabel', '[]Minimum').
            in('inside').
            in('inside').
            project('minimum').by(values('value')),
            select('val').
            in('inside').
            has('VertexLabel', '[]Maximum').
            in('inside').
            in('inside').
            project('maximum').by(values('value')),
            select('val').
            in('inside').
            has('VertexLabel', '[]AssignedValue').
            in('inside').
            in('inside').
            project('assigned').by(values('value'))).
          unfold().
          group().by(select(keys)).by(select(values)))).
    by(
      __.in('inside').
      has('VertexLabel', '[]Connector').
      values('[]Name').
      order().
      fold()).
  order().by('class').by('model')