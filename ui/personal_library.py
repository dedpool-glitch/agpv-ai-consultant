"""Upload and manage the local searchable PDF library."""

from services.personal_library import add_pdf, list_documents, remove_document


def render_personal_library(key_prefix):
    import streamlit as st

    added_name = st.session_state.pop(f"{key_prefix}_personal_added", None)
    if added_name:
        st.toast(f"Added {added_name} to My library.")
    try:
        documents = list_documents()
        library_error = False
    except Exception:
        documents = []
        library_error = True
    label = f"My library ({len(documents)})" if documents else "My library"
    with st.popover(label, icon=":material/folder_open:"):
        st.caption("Your PDFs are saved on this computer for this Windows account.")
        upload = st.file_uploader(
            "Add a searchable PDF", type=["pdf"], max_upload_size=20,
            key=f"{key_prefix}_personal_pdf"
        )
        if st.button("Add to My library", disabled=upload is None,
                     key=f"{key_prefix}_personal_add"):
            try:
                with st.spinner("Reading and indexing the PDF..."):
                    result = add_pdf(upload.name, upload.getvalue())
            except ValueError as error:
                st.error(str(error))
            except Exception:
                st.error("The PDF could not be indexed. Your existing library is unchanged.")
            else:
                if result["already_present"]:
                    st.info("This PDF is already in My library.")
                else:
                    st.session_state[f"{key_prefix}_personal_added"] = upload.name
                    st.rerun()

        if library_error:
            st.error("My library could not be opened.")
            return
        if not documents:
            st.caption("No PDFs added yet.")
        else:
            st.markdown("**Saved PDFs**")
            for document in documents:
                title_column, remove_column = st.columns([4, 1], vertical_alignment="center")
                with title_column:
                    st.write(f"{document['title']} · {document['page_count']} pages")
                with remove_column:
                    if st.button("Remove", key=f"{key_prefix}_remove_{document['document_id']}"):
                        try:
                            remove_document(document["document_id"])
                        except Exception:
                            st.error("Could not remove this PDF. Please try again.")
                        else:
                            st.rerun()
        with st.expander("How this works"):
            st.caption("My library is separate from the shared CEED research library.")
            st.caption("Matching excerpts may be sent to the AI service when you ask a question.")
            st.caption("While PDFs are saved here, conversation logs stay on this computer instead of going to the shared research sheet.")


def render_retrieved_sources(chunks):
    """Show where retrieved answer context came from without exposing the excerpts."""
    if not chunks:
        return
    import streamlit as st

    seen = set()
    with st.expander("Retrieved sources", expanded=False):
        for chunk in chunks:
            metadata = chunk.get("metadata") or {}
            source = metadata.get("library") or "CEED library"
            title = metadata.get("title") or "Unknown document"
            page = metadata.get("page")
            item = (source, title, page)
            if item in seen:
                continue
            seen.add(item)
            st.write(f"{source}: {title}" + (f", p. {page}" if page else ""))
