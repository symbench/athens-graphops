g.V().
  has('VertexLabel', '[]Classifications').as('class').
  in('inside').
  has('value', '__CLASSIFICATION__').
  select('class').
  out('inside').
  has('VertexLabel', '[avm]Component').as('comp').
  map(
    union(
      project('MODEL_NAME').by('[]Name'),
      __.in('inside').
      has('VertexLabel', '[]Property').as('prop').
      in('inside').
      in('inside').
      has(
        '[http://www.w3.org/2001/XMLSchema-instance]type',
        '[avm]FixedValue').
      in('inside').
      in('inside').as('val').
      group().
        by(select('prop').by('[]Name')).
        by(select('val').by('value'))).
    unfold().
    group().by(select(keys)).by(select(values))).
  order().by('MODEL_NAME')