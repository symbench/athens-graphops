g.V().
  has('VertexLabel', '[]Classifications').as('class').
  out('inside').
  has('VertexLabel', '[avm]Component').
  has('[]Name', '__MODEL_NAME__').as('comp').
  project(
    'class',
    'model',
    'id',
    'properties',
    'parameters',
    'connectors').
    by(select('class').in('inside').values('value')).
    by('[]Name').
    by('[]ID').
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
            project('maximum').by(values('value'))).
          unfold().
          group().by(select(keys)).by(select(values)))).
    by(
      __.in('inside').has('VertexLabel', '[]Connector').values('[]Name'))
