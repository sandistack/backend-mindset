# 🔍 Step 7: Search Engine

**Waktu:** 6-8 jam  
**Prerequisite:** Step 6 selesai

---

## 🎯 Tujuan

- Elasticsearch integration
- Full-text search untuk documents, messages, files
- Faceted search & filters
- Search suggestions
- Real-time indexing

---

## 📋 Tasks

### 7.1 Elasticsearch Documents

**Buat `apps/search/documents.py`:**

```python
from elasticsearch_dsl import Document, Text, Keyword, Date, Integer, Nested, Object, analyzer, tokenizer

# Custom analyzer for better search
autocomplete_analyzer = analyzer(
    'autocomplete',
    tokenizer=tokenizer('autocomplete_tokenizer', 'edge_ngram', min_gram=2, max_gram=10),
    filter=['lowercase']
)

class DocumentIndex(Document):
    """Elasticsearch document for Documents"""
    
    title = Text(analyzer='standard', fields={
        'autocomplete': Text(analyzer=autocomplete_analyzer),
        'keyword': Keyword()
    })
    content = Text(analyzer='standard')
    
    workspace_id = Keyword()
    created_by_id = Keyword()
    created_by_name = Text()
    
    created_at = Date()
    updated_at = Date()
    
    class Index:
        name = 'documents'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }


class MessageIndex(Document):
    """Elasticsearch document for Messages"""
    
    content = Text(analyzer='standard')
    
    channel_id = Keyword()
    channel_name = Text()
    workspace_id = Keyword()
    
    user_id = Keyword()
    user_name = Text()
    
    created_at = Date()
    
    class Index:
        name = 'messages'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }


class FileIndex(Document):
    """Elasticsearch document for Files"""
    
    name = Text(analyzer='standard', fields={
        'autocomplete': Text(analyzer=autocomplete_analyzer),
        'keyword': Keyword()
    })
    description = Text(analyzer='standard')
    
    workspace_id = Keyword()
    folder_path = Text()
    mime_type = Keyword()
    
    uploaded_by_id = Keyword()
    uploaded_by_name = Text()
    
    size = Integer()
    created_at = Date()
    
    tags = Keyword(multi=True)
    
    class Index:
        name = 'files'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
```

### 7.2 Search Service

**Buat `apps/search/services.py`:**

```python
from elasticsearch_dsl import Q, Search
from django.conf import settings
from .documents import DocumentIndex, MessageIndex, FileIndex

class SearchService:
    
    # Index operations
    @classmethod
    def index_document(cls, document):
        """Index a document"""
        doc = DocumentIndex(
            meta={'id': str(document.id)},
            title=document.title,
            content=document.content,
            workspace_id=str(document.workspace_id),
            created_by_id=str(document.created_by_id) if document.created_by else None,
            created_by_name=document.created_by.name if document.created_by else None,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        doc.save()
    
    @classmethod
    def index_message(cls, message):
        """Index a message"""
        doc = MessageIndex(
            meta={'id': str(message.id)},
            content=message.content,
            channel_id=str(message.channel_id),
            channel_name=message.channel.name,
            workspace_id=str(message.channel.workspace_id),
            user_id=str(message.user_id),
            user_name=message.user.name,
            created_at=message.created_at
        )
        doc.save()
    
    @classmethod
    def index_file(cls, file):
        """Index a file"""
        doc = FileIndex(
            meta={'id': str(file.id)},
            name=file.name,
            description=file.description,
            workspace_id=str(file.workspace_id),
            folder_path=file.folder.path if file.folder else '',
            mime_type=file.mime_type,
            uploaded_by_id=str(file.uploaded_by_id) if file.uploaded_by else None,
            uploaded_by_name=file.uploaded_by.name if file.uploaded_by else None,
            size=file.size,
            created_at=file.created_at,
            tags=file.tags
        )
        doc.save()
    
    @classmethod
    def delete_index(cls, index_class, id):
        """Delete from index"""
        try:
            doc = index_class.get(id=id)
            doc.delete()
        except:
            pass
    
    # Search operations
    @classmethod
    def search_all(cls, workspace_id, query, page=1, size=20):
        """Search across all content types"""
        results = {
            'documents': [],
            'messages': [],
            'files': [],
            'total': 0
        }
        
        # Search documents
        doc_results = cls.search_documents(workspace_id, query, page=1, size=5)
        results['documents'] = doc_results['hits']
        
        # Search messages
        msg_results = cls.search_messages(workspace_id, query, page=1, size=5)
        results['messages'] = msg_results['hits']
        
        # Search files
        file_results = cls.search_files(workspace_id, query, page=1, size=5)
        results['files'] = file_results['hits']
        
        results['total'] = (
            doc_results['total'] + 
            msg_results['total'] + 
            file_results['total']
        )
        
        return results
    
    @classmethod
    def search_documents(cls, workspace_id, query, page=1, size=20):
        """Search documents"""
        s = DocumentIndex.search()
        
        # Filter by workspace
        s = s.filter('term', workspace_id=str(workspace_id))
        
        # Search query
        if query:
            s = s.query(
                Q('multi_match', query=query, fields=['title^3', 'content'], fuzziness='AUTO') |
                Q('match_phrase_prefix', title=query)
            )
        
        # Pagination
        start = (page - 1) * size
        s = s[start:start + size]
        
        # Highlighting
        s = s.highlight('title', 'content', fragment_size=150)
        
        response = s.execute()
        
        return cls._format_results(response)
    
    @classmethod
    def search_messages(cls, workspace_id, query, channel_id=None, page=1, size=20):
        """Search messages"""
        s = MessageIndex.search()
        
        s = s.filter('term', workspace_id=str(workspace_id))
        
        if channel_id:
            s = s.filter('term', channel_id=str(channel_id))
        
        if query:
            s = s.query('match', content={'query': query, 'fuzziness': 'AUTO'})
        
        s = s.sort('-created_at')
        
        start = (page - 1) * size
        s = s[start:start + size]
        
        s = s.highlight('content', fragment_size=150)
        
        response = s.execute()
        
        return cls._format_results(response)
    
    @classmethod
    def search_files(cls, workspace_id, query, mime_type=None, page=1, size=20):
        """Search files"""
        s = FileIndex.search()
        
        s = s.filter('term', workspace_id=str(workspace_id))
        
        if mime_type:
            s = s.filter('prefix', mime_type=mime_type)
        
        if query:
            s = s.query(
                Q('multi_match', query=query, fields=['name^2', 'description', 'tags']) |
                Q('match_phrase_prefix', name=query)
            )
        
        start = (page - 1) * size
        s = s[start:start + size]
        
        s = s.highlight('name', 'description')
        
        response = s.execute()
        
        return cls._format_results(response)
    
    @classmethod
    def suggest(cls, workspace_id, query, size=5):
        """Get search suggestions (autocomplete)"""
        s = DocumentIndex.search()
        
        s = s.filter('term', workspace_id=str(workspace_id))
        s = s.query('match_phrase_prefix', title__autocomplete=query)
        s = s[:size]
        s = s.source(['title'])
        
        response = s.execute()
        
        return [hit.title for hit in response]
    
    @staticmethod
    def _format_results(response):
        """Format search results"""
        hits = []
        
        for hit in response:
            item = hit.to_dict()
            item['id'] = hit.meta.id
            item['score'] = hit.meta.score
            
            if hasattr(hit.meta, 'highlight'):
                item['highlights'] = dict(hit.meta.highlight)
            
            hits.append(item)
        
        return {
            'hits': hits,
            'total': response.hits.total.value
        }
```

### 7.3 Indexing Tasks

**Buat `apps/search/tasks.py`:**

```python
from celery import shared_task
from apps.core.tasks import BaseTask
from .services import SearchService

@shared_task(base=BaseTask)
def index_document_task(document_id):
    """Index document async"""
    from apps.documents.models import Document
    
    try:
        document = Document.objects.get(id=document_id)
        SearchService.index_document(document)
    except Document.DoesNotExist:
        pass


@shared_task(base=BaseTask)
def index_message_task(message_id):
    """Index message async"""
    from apps.channels.models import Message
    
    try:
        message = Message.objects.select_related('channel', 'user').get(id=message_id)
        SearchService.index_message(message)
    except Message.DoesNotExist:
        pass


@shared_task(base=BaseTask)
def index_file_task(file_id):
    """Index file async"""
    from apps.files.models import File
    
    try:
        file = File.objects.select_related('folder', 'uploaded_by').get(id=file_id)
        SearchService.index_file(file)
    except File.DoesNotExist:
        pass


@shared_task(base=BaseTask)
def full_reindex():
    """Full reindex all content"""
    from apps.documents.models import Document
    from apps.channels.models import Message
    from apps.files.models import File
    
    # Recreate indices
    from .documents import DocumentIndex, MessageIndex, FileIndex
    
    for index in [DocumentIndex, MessageIndex, FileIndex]:
        index._index.delete(ignore=404)
        index.init()
    
    # Index all documents
    for doc in Document.objects.select_related('created_by').iterator():
        SearchService.index_document(doc)
    
    # Index all messages
    for msg in Message.objects.select_related('channel', 'user').iterator():
        SearchService.index_message(msg)
    
    # Index all files
    for file in File.objects.select_related('folder', 'uploaded_by').iterator():
        SearchService.index_file(file)
```

### 7.4 Signals for Auto-indexing

**Buat `apps/search/signals.py`:**

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .tasks import index_document_task, index_message_task, index_file_task
from .services import SearchService
from .documents import DocumentIndex, MessageIndex, FileIndex

@receiver(post_save, sender='documents.Document')
def index_document_on_save(sender, instance, **kwargs):
    index_document_task.delay(str(instance.id))


@receiver(post_delete, sender='documents.Document')
def delete_document_from_index(sender, instance, **kwargs):
    SearchService.delete_index(DocumentIndex, str(instance.id))


@receiver(post_save, sender='channels.Message')
def index_message_on_save(sender, instance, **kwargs):
    index_message_task.delay(str(instance.id))


@receiver(post_delete, sender='channels.Message')
def delete_message_from_index(sender, instance, **kwargs):
    SearchService.delete_index(MessageIndex, str(instance.id))


@receiver(post_save, sender='files.File')
def index_file_on_save(sender, instance, **kwargs):
    index_file_task.delay(str(instance.id))


@receiver(post_delete, sender='files.File')
def delete_file_from_index(sender, instance, **kwargs):
    SearchService.delete_index(FileIndex, str(instance.id))
```

### 7.5 Views

```python
from rest_framework.views import APIView
from rest_framework.response import Response

class GlobalSearchView(APIView):
    """Search across all content types"""
    
    def get(self, request, workspace_slug):
        workspace = get_object_or_404(Workspace, slug=workspace_slug)
        
        query = request.query_params.get('q', '')
        page = int(request.query_params.get('page', 1))
        
        results = SearchService.search_all(
            workspace_id=workspace.id,
            query=query,
            page=page
        )
        
        return Response(results)


class DocumentSearchView(APIView):
    """Search documents only"""
    
    def get(self, request, workspace_slug):
        workspace = get_object_or_404(Workspace, slug=workspace_slug)
        
        query = request.query_params.get('q', '')
        page = int(request.query_params.get('page', 1))
        
        results = SearchService.search_documents(
            workspace_id=workspace.id,
            query=query,
            page=page
        )
        
        return Response(results)


class MessageSearchView(APIView):
    """Search messages"""
    
    def get(self, request, workspace_slug):
        workspace = get_object_or_404(Workspace, slug=workspace_slug)
        
        query = request.query_params.get('q', '')
        channel_id = request.query_params.get('channel')
        page = int(request.query_params.get('page', 1))
        
        results = SearchService.search_messages(
            workspace_id=workspace.id,
            query=query,
            channel_id=channel_id,
            page=page
        )
        
        return Response(results)


class FileSearchView(APIView):
    """Search files"""
    
    def get(self, request, workspace_slug):
        workspace = get_object_or_404(Workspace, slug=workspace_slug)
        
        query = request.query_params.get('q', '')
        mime_type = request.query_params.get('type')
        page = int(request.query_params.get('page', 1))
        
        results = SearchService.search_files(
            workspace_id=workspace.id,
            query=query,
            mime_type=mime_type,
            page=page
        )
        
        return Response(results)


class SuggestView(APIView):
    """Get search suggestions"""
    
    def get(self, request, workspace_slug):
        workspace = get_object_or_404(Workspace, slug=workspace_slug)
        
        query = request.query_params.get('q', '')
        
        suggestions = SearchService.suggest(
            workspace_id=workspace.id,
            query=query
        )
        
        return Response({'suggestions': suggestions})
```

---

## ✅ Checklist

- [ ] Elasticsearch documents (indices)
- [ ] Custom analyzers untuk autocomplete
- [ ] SearchService dengan indexing
- [ ] Multi-field search
- [ ] Highlighting
- [ ] Pagination
- [ ] Indexing tasks
- [ ] Signal-based auto-indexing
- [ ] Full reindex task
- [ ] Search API endpoints
- [ ] Suggestions API

---

## 🔗 Referensi

- Elasticsearch DSL: https://elasticsearch-dsl.readthedocs.io/

---

## ➡️ Next Step

Lanjut ke [08-DEPLOYMENT.md](08-DEPLOYMENT.md) - Production Deployment
