
def parse_parser_xml_results(xml, file_name="", raw_output=False):
    "THIS METHOD STOLEN FROM corenlp.py"
    import xmltodict
    from collections import OrderedDict

    def enforceList(list_or_ordered_dict): #TIM
        if type(list_or_ordered_dict) == type(OrderedDict()):
            return [list_or_ordered_dict]
        else:
            return list_or_ordered_dict

    def extract_words_from_xml(sent_node):
        if type(sent_node['tokens']['token']) == type(OrderedDict()):
            # This is also specific case of xmltodict
            exted = [sent_node['tokens']['token']]
        else:
            exted = sent_node['tokens']['token']
        exted_string = map(lambda x: x['word'], exted)
        return exted_string

    # Turning the raw xml into a raw python dictionary:
    raw_dict = xmltodict.parse(xml)
    if raw_output:
        return raw_dict

    document = raw_dict[u'root'][u'document']

    # Making a raw sentence list of dictionaries:
    raw_sent_list = document[u'sentences'][u'sentence']

    if document.get(u'coreference') and document[u'coreference'].get(u'coreference'):
        # Convert coreferences to the format like python
        coref_flag = True

        # Making a raw coref dictionary:
        raw_coref_list = document[u'coreference'][u'coreference']

        # It is specific case that there is only one item for xmltodict
        if len(raw_coref_list) == 1:
            raw_coref_list = [raw_coref_list]
        if len(raw_sent_list) == 1:
            raw_sent_list = [raw_sent_list]

        # This is also specific case of xmltodict
        raw_sent_list = enforceList(raw_sent_list)

        # To dicrease is for given index different from list index
        coref_index = [[[int(raw_coref_list[j]['mention'][i]['sentence']) - 1,
                         int(raw_coref_list[j]['mention'][i]['head']) - 1,
                         int(raw_coref_list[j]['mention'][i]['start']) - 1,
                         int(raw_coref_list[j]['mention'][i]['end']) - 1]
                        for i in xrange(len(raw_coref_list[j][u'mention']))]
                       for j in xrange(len(raw_coref_list))]

        coref_list = []
        for j in xrange(len(coref_index)):
            coref_list.append(coref_index[j])
            for k, coref in enumerate(coref_index[j]):
                if type(raw_sent_list[coref[0]]['tokens']['token']) == type(OrderedDict()):
                    # This is also specific case of xmltodict
                    exted = [raw_sent_list[coref[0]]['tokens']['token']]
                else:
                    exted = raw_sent_list[coref[0]]['tokens']['token'][coref[2]:coref[3]]
                exted_words = map(lambda x: x['word'], exted)
                coref_list[j][k].insert(0, ' '.join(exted_words))

        coref_list = [[[coref_list[j][i], coref_list[j][0]]
                       for i in xrange(len(coref_list[j])) if i != 0]
                      for j in xrange(len(coref_list))]
    else:
        coref_flag = False

    # This is also specific case of xmltodict
    raw_sent_list = enforceList(raw_sent_list)

    sentences = []
    for id in xrange(len(raw_sent_list)):
        sent = {}
        sent['text'] = extract_words_from_xml(raw_sent_list[id])
        sent['parsetree'] = unicode(raw_sent_list[id]['parse'])
        # sent['sentimentValue'] = int(raw_sent_list[id].get(['@sentimentValue'])) # TIM
        # sent['sentiment'] = raw_sent_list[id]['@sentiment'] # TIM
        sentiment_value = raw_sent_list[id].get('@sentimentValue')
        sentiment = raw_sent_list[id].get('@sentiment')
        if sentiment_value: sent['sentimentValue'] = int(sentiment_value)
        if sentiment_value: sent['sentiment'] = sentiment
        
        if type(raw_sent_list[id]['tokens']['token']) == type(OrderedDict()):
            # This is also specific case of xmltodict
            token = raw_sent_list[id]['tokens']['token']
            sent['words'] = [
                [unicode(token['word']), OrderedDict([
                    ('NamedEntityTag', str(token['NER'])),
                    ('CharacterOffsetEnd', str(token['CharacterOffsetEnd'])),
                    ('CharacterOffsetBegin', str(token['CharacterOffsetBegin'])),
                    ('PartOfSpeech', str(token['POS'])),
                    ('Lemma', unicode(token['lemma']))])]
            ]
        else:
            sent['words'] = [[unicode(token['word']), OrderedDict([
                ('NamedEntityTag', str(token['NER'])),
                ('CharacterOffsetEnd', str(token['CharacterOffsetEnd'])),
                ('CharacterOffsetBegin', str(token['CharacterOffsetBegin'])),
                ('PartOfSpeech', str(token['POS'])),
                ('Lemma', unicode(token['lemma']))])]
                             for token in raw_sent_list[id]['tokens']['token']]
        
        DEP_SOURCE = "collapsed-ccprocessed-dependencies"

        sent['dependencies'] = [[enforceList(dep['dep'])[i]['@type'],
                                 enforceList(dep['dep'])[i]['governor']['#text'],
                                 enforceList(dep['dep'])[i]['dependent']['#text']]
                                for dep in raw_sent_list[id]['dependencies'] if dep.get('dep')
                                for i in xrange(len(enforceList(dep['dep'])))
                                if dep['@type'] == DEP_SOURCE]

        # Added by DES -- parallels dependencies, but opens up as 
        # a for loop to make more hackable
        # What a fucking mess.
    

        sent['indexeddependencies'] = []
        for dep in raw_sent_list[id]["dependencies"]:
            if dep.get("dep"):
                dep_crap = enforceList(dep["dep"]) 
                indexed = lambda kind: "-".join([dep_crap[i][kind]["#text"], 
                                                dep_crap[i][kind]["@idx"]])
                for i in xrange(len(dep_crap)):
                    if dep["@type"] == DEP_SOURCE:
                        shit = [dep_crap[i]["@type"], 
                                indexed("governor"), 
                                indexed("dependent")]
                        sent["indexeddependencies"].append(shit)

        sentences.append(sent)

    if coref_flag:
        results = {'coref': coref_list, 'sentences': sentences}
    else:
        results = {'sentences': sentences}

    if file_name:
        results['file_name'] = file_name

    return results


