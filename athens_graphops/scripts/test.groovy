// g.V().has('VertexLabel', '[avm]Component').limit(1).in('inside').label()
// g.V().has('VertexLabel', '[avm]Component').as('comp').limit(1).in('inside').has('VertexLabel', '[]Property').as('prop').select('comp', 'prop').by(elementMap()).by(values('[]Name'))
// g.V().has('VertexLabel', '[avm]Component').limit(20).as('comp').project('name', 'properties').by('[]Name').by(select('comp').in('inside').has('VertexLabel', '[]Connector').valueMap().fold())
// g.V().has('VertexLabel', '[]Classifications').as('class').in('inside').as('class_name').select('class').out('inside').has('VertexLabel', '[avm]Component').as('comp').limit(2).project('type', 'name', 'id', 'schema_version').by(select('class_name').values('value')).by('[]Name').by('[]ID').by('[]SchemaVersion')
// g.V().has('VertexLabel', '[]Classifications').as('class').in('inside').as('class_name').select('class').out('inside').has('VertexLabel', '[avm]Component').as('comp').project('type', 'name', 'id').by(select('class_name').values('value')).by('[]Name').by('[]ID')
// g.V().has('VertexLabel', '[avm]Component').limit(20).as('comp').project('name', 'labels').by('[]Name').by(select('comp').in('inside').values('VertexLabel').fold())
//g.V().has('VertexLabel', '[]Classifications').as('class').in('inside').has('value', 'Propeller').select('class').out('inside').has('VertexLabel','[avm]Component').as('comp').limit(1).in('inside').has('VertexLabel', '[]Property').as('prop').in('inside').in('inside').has('[http://www.w3.org/2001/XMLSchema-instance]type', '[avm]FixedValue').in('inside').in('inside').as('val').project('key', 'val').by(select('prop').by('[]Name')).by(select('val').by('value'))
// g.V().has('VertexLabel', '[]Classifications').as('class').in('inside').has('value', 'Propeller').select('class').out('inside').has('VertexLabel','[avm]Component').as('comp').limit(2).elementMap()
//g.V().has('VertexLabel', '[]Classifications').as('class').in('inside').has('value', 'Propeller').select('class').out('inside').has('VertexLabel','[avm]Component').limit(3).as('comp').select('comp').in('inside').has('VertexLabel', '[]Property').as('prop').in('inside').in('inside').has('[http://www.w3.org/2001/XMLSchema-instance]type', '[avm]FixedValue').in('inside').in('inside').as('val').group().by(select('prop').by('[]Name')).by(select('val').by('value').count())
// g.V().has('VertexLabel', '[]Classifications').as('class').in('inside').has('value', 'Propeller').select('class').out('inside').has('VertexLabel','[avm]Component').limit(3).as('comp').map(select('comp').in('inside').has('VertexLabel', '[]Property').as('prop').in('inside').in('inside').has('[http://www.w3.org/2001/XMLSchema-instance]type', '[avm]FixedValue').in('inside').in('inside').as('val').group().by(select('prop').by('[]Name')).by(select('val').by('value')))

// g.V().has('VertexLabel', '[]Classifications').as('class').in('inside').as('class_name').select('class').out('inside').has('VertexLabel', '[avm]Component').limit(3).as('comp').project('type', 'name', 'id', 'properties', 'connectors').by(select('class_name').values('value')).by('[]Name').by('[]ID').by(select('comp').in('inside').has('VertexLabel', '[]Property').as('prop').in('inside').in('inside').has('[http://www.w3.org/2001/XMLSchema-instance]type', '[avm]FixedValue').in('inside').in('inside').as('val').group().by(select('prop').by('[]Name')).by(select('val').by('value'))).by(select('comp').in('inside').has('VertexLabel', '[]Connector').values('[]Name').order().fold()).order().by('type').by('name')
// g.V().has('VertexLabel', '[]Classifications').as('class').in('inside').has('value', 'Propeller').select('class').out('inside').has('VertexLabel','[avm]Component').as('comp').limit(2).map(union(project('COMPONENT').by('[]Name'),__.in('inside').has('VertexLabel', '[]Property').as('prop').in('inside').in('inside').has('[http://www.w3.org/2001/XMLSchema-instance]type', '[avm]FixedValue').in('inside').in('inside').as('val').group().by(select('prop').by('[]Name')).by(select('val').by('value'))).unfold().group().by(select(keys)).by(select(values)))

g.V().has('VertexLabel', '[]Classifications')
