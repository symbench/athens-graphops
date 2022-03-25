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
    'properties',
    'parameters',
    'connectors').
    by(select('class_name').values('value')).
    by('[]Name').
    by('[]ID').
    by(
      select('comp').
      in("inside").
      has('VertexLabel', '[]Property').as('prop').
      in("inside").
      in("inside").
      has(
        "[http://www.w3.org/2001/XMLSchema-instance]type",
        "[avm]FixedValue").
      in("inside").
      in("inside").as("val").
      group().
        by(select('prop').by('[]Name')).
        by(select('val').by('value'))).
    by(
      select('comp').
      in("inside").
      has('VertexLabel', '[]Property').as('prop').
      in("inside").
      in("inside").
      has(
        "[http://www.w3.org/2001/XMLSchema-instance]type",
        "[avm]ParametricValue").
      in("inside").as("type").
      group().
        by(select("prop").by("[]Name")).
        by(
          select("type").
          group().
            by(label).
            by(
              select("type").
              in("inside").
              in('inside').as("valueNode").
              select("valueNode").by("value")))).
    by(
      select('comp').
      in('inside').
      has('VertexLabel', '[]Connector').
      values('[]Name').
      order().
      fold()).
  order().by('type').by('name')
